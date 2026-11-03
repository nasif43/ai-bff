"""
Server Module for Live AI BFF.
Provides WebSocket endpoints, HTTP static asset delivery, and multi-client broadcast.
"""

import os
import json
import socket
import asyncio
from typing import Dict, Any
from aiohttp import web, WSMsgType
import qrcode

from config import (
    SERVER_HOST,
    SERVER_PORT,
    STATIC_DIR,
    AUDIO_DIR,
    VALID_ARCHETYPES,
    VALID_ATTITUDES,
    VALID_GENDERS,
)
from groq_engine import GroqEngine
from tts_engine import TTSEngine

groq_engine = GroqEngine()
tts_engine = TTSEngine()

# Connected clients state: {ws: {"archetype": str, "attitude": str, "gender": str, "history": list}}
connected_clients: Dict[web.WebSocketResponse, Dict[str, Any]] = {}

def get_lan_ip() -> str:
    """Finds the outward-facing local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def print_banner(host: str, port: int):
    lan_ip = get_lan_ip()
    url = f"http://{lan_ip}:{port}"
    print("\n" + "=" * 60)
    print(" 🎭 LIVE AI BFF - STAGE INTERACTION ENGINE")
    print("=" * 60)
    print(f" Local URL:   http://localhost:{port}")
    print(f" Network URL: {url}")
    print(f" WebSocket:   ws://{lan_ip}:{port}/ws")
    print("=" * 60)
    print(" Scan QR code below on your phone to open the controller:")
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.print_ascii(invert=True)
    print("=" * 60 + "\n")

async def broadcast(message: Dict[str, Any]):
    """Broadcasts a JSON message to all active WebSocket connections."""
    if not connected_clients:
        return
    payload = json.dumps(message)
    dead_clients = []
    for ws in list(connected_clients.keys()):
        try:
            if not ws.closed:
                await ws.send_str(payload)
            else:
                dead_clients.append(ws)
        except Exception:
            dead_clients.append(ws)

    for ws in dead_clients:
        if ws in connected_clients:
            del connected_clients[ws]

async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Initial default configuration for this client
    connected_clients[ws] = {
        "archetype": "DarkSoul",
        "attitude": "Delulu",
        "gender": "M",
        "history": [],
    }
    print(f"[WS] Client connected. Total active: {len(connected_clients)}")

    # Send initial welcome & config state
    await ws.send_str(json.dumps({
        "event": "connected",
        "message": "Connected to Live AI BFF Engine",
        "config": {
            "archetype": "DarkSoul",
            "attitude": "Delulu",
            "gender": "M",
        }
    }))

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception as e:
                    await ws.send_str(json.dumps({"event": "error", "message": f"Invalid JSON: {e}"}))
                    continue

                action = data.get("action")

                # Handle configuration change
                if action == "set_config":
                    if "archetype" in data and data["archetype"] in VALID_ARCHETYPES:
                        connected_clients[ws]["archetype"] = data["archetype"]
                    if "attitude" in data and data["attitude"] in VALID_ATTITUDES:
                        connected_clients[ws]["attitude"] = data["attitude"]
                    if "gender" in data and data["gender"] in VALID_GENDERS:
                        connected_clients[ws]["gender"] = data["gender"]

                    print(f"[WS] Config updated: {connected_clients[ws]['archetype']} x "
                          f"{connected_clients[ws]['attitude']} ({connected_clients[ws]['gender']})")

                    await ws.send_str(json.dumps({
                        "event": "config_updated",
                        "config": {
                            "archetype": connected_clients[ws]["archetype"],
                            "attitude": connected_clients[ws]["attitude"],
                            "gender": connected_clients[ws]["gender"],
                        }
                    }))
                    continue

                # Handle reset conversation history
                if action == "reset_context":
                    connected_clients[ws]["history"] = []
                    await ws.send_str(json.dumps({"event": "context_reset", "message": "History cleared"}))
                    continue

                # Handle audio stop / interrupt
                if action == "stop_audio":
                    print("[WS] Stop audio broadcast requested")
                    await broadcast({"event": "audio_stopped"})
                    continue

                # Process spoken / text input turn
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                client_state = connected_clients[ws]
                arch = client_state["archetype"]
                att = client_state["attitude"]
                gender = client_state["gender"]

                print(f"[Turn] User ({arch} x {att}): {user_text}")

                # Notify clients that LLM processing has started
                await broadcast({
                    "event": "status",
                    "state": "generating_llm",
                    "user_text": user_text,
                })

                # Run Groq LLM in thread pool to avoid blocking async loop
                loop = asyncio.get_event_loop()
                reply_text, emotion = await loop.run_in_executor(
                    None,
                    groq_engine.generate_turn,
                    user_text,
                    client_state["history"],
                    arch,
                    att,
                )

                print(f"[Turn] BFF ({emotion}): {reply_text}")

                # Maintain history
                client_state["history"].append({"role": "user", "content": user_text})
                client_state["history"].append({"role": "assistant", "content": reply_text})
                # Keep last 10 messages to maintain latency & context freshness
                if len(client_state["history"]) > 10:
                    client_state["history"] = client_state["history"][-10:]

                # Notify clients that TTS generation has started
                await broadcast({
                    "event": "status",
                    "state": "generating_tts",
                    "text": reply_text,
                    "emotion": emotion,
                })

                # Run ElevenLabs TTS in thread pool
                tts_result = await loop.run_in_executor(
                    None,
                    tts_engine.convert_with_timestamps,
                    reply_text,
                    arch,
                    gender,
                )

                if "error" in tts_result:
                    await ws.send_str(json.dumps({
                        "event": "error",
                        "message": f"TTS generation error: {tts_result['error']}",
                    }))
                    continue

                # Broadcast completed turn payload to all connected clients (Visualizer, Controllers)
                turn_payload = {
                    "event": "turn_complete",
                    "user_text": user_text,
                    "text": reply_text,
                    "emotion": emotion,
                    "audio_url": tts_result["audio_url"],
                    "timestamps": tts_result["timestamps"],
                    "duration": tts_result["duration"],
                    "archetype": arch,
                    "attitude": att,
                    "gender": gender,
                }

                await broadcast(turn_payload)

            elif msg.type == WSMsgType.ERROR:
                print(f"[WS] WebSocket error: {ws.exception()}")

    except Exception as e:
        print(f"[WS] Exception in client loop: {e}")
    finally:
        if ws in connected_clients:
            del connected_clients[ws]
            print(f"[WS] Client disconnected. Total active: {len(connected_clients)}")

    return ws

async def index_handler(request: web.Request):
    return web.FileResponse(os.path.join(STATIC_DIR, "index.html"))

async def stt_handler(request: web.Request) -> web.Response:
    """Handles audio file uploads for Groq Whisper STT fallback."""
    try:
        reader = await request.multipart()
        field = await reader.next()
        if field and field.name == "audio":
            audio_bytes = await field.read()
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None, groq_engine.transcribe_audio, audio_bytes, "recording.webm"
            )
            return web.json_response({"text": transcription})
        return web.json_response({"error": "No audio field provided"}, status=400)
    except Exception as e:
        print(f"[STT] Exception: {e}")
        return web.json_response({"error": str(e)}, status=500)

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_post("/api/stt", stt_handler)
    app.router.add_static("/static", STATIC_DIR, show_index=False)
    app.router.add_static("/audio", AUDIO_DIR, show_index=False)
    return app

if __name__ == "__main__":
    print_banner(SERVER_HOST, SERVER_PORT)
    app = create_app()
    web.run_app(app, host=SERVER_HOST, port=SERVER_PORT)
