"""
Server Module for Live AI BFF.
Provides WebSocket endpoints, HTTP static asset delivery, multi-client broadcast,
and automatic Cloudflare HTTPS Tunnel orchestration.
"""

import os
import sys
import json
import time
import socket
import asyncio
import atexit
import shutil
import re
import subprocess
import threading
from typing import Dict, Any, Optional
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

tunnel_process: Optional[subprocess.Popen] = None
public_https_url: Optional[str] = None

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

def start_cloudflare_tunnel(port: int) -> Optional[str]:
    """Launches a Cloudflare quick tunnel and captures the public HTTPS URL."""
    global tunnel_process
    cf_bin = shutil.which("cloudflared") or "/home/muhts/.local/bin/cloudflared"
    if not os.path.exists(cf_bin):
        print("[Tunnel] cloudflared not found, skipping tunnel setup.")
        return None

    try:
        print(f"[Tunnel] Launching Cloudflare Tunnel for port {port}...")
        tunnel_process = subprocess.Popen(
            [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        def cleanup_tunnel():
            if tunnel_process and tunnel_process.poll() is None:
                print("[Tunnel] Stopping Cloudflare Tunnel...")
                tunnel_process.terminate()

        atexit.register(cleanup_tunnel)

        # Monitor stderr to extract the trycloudflare.com URL
        url_match = None
        start_time = time.time()
        while time.time() - start_time < 12:
            line = tunnel_process.stderr.readline()
            if not line:
                if tunnel_process.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m:
                url_match = m.group(0)
                break

        return url_match
    except Exception as e:
        print(f"[Tunnel] Failed to start tunnel: {e}")
        return None

def print_banner(host: str, port: int, https_url: Optional[str] = None):
    lan_ip = get_lan_ip()
    local_url = f"http://localhost:{port}"
    lan_url = f"http://{lan_ip}:{port}"
    primary_url = https_url if https_url else lan_url

    print("\n" + "=" * 65)
    print(" 🎭 LIVE AI BFF - STAGE INTERACTION ENGINE (CLOUDFLARE SECURE)")
    print("=" * 65)
    print(f" Local URL:       {local_url}")
    print(f" LAN URL:         {lan_url}")
    if https_url:
        print(f" HTTPS Tunnel:    {https_url}  (Microphone Authorized)")
        print(f" WSS WebSocket:   wss://{https_url.replace('https://', '')}/ws")
    else:
        print(f" WebSocket:       ws://{lan_ip}:{port}/ws")
    print("=" * 65)
    print(" Scan QR code below on your phone to open the controller instantly:")
    qr = qrcode.QRCode(border=1)
    qr.add_data(primary_url)
    qr.print_ascii(invert=True)
    print("=" * 65 + "\n")

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
        "audio_route": "both",
        "history": [],
    }
    print(f"[WS] Client connected. Total active: {len(connected_clients)}")

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
                    if "audio_route" in data:
                        connected_clients[ws]["audio_route"] = data["audio_route"]

                    print(f"[WS] Config updated: {connected_clients[ws]['archetype']} x "
                          f"{connected_clients[ws]['attitude']} ({connected_clients[ws]['gender']}) "
                          f"[route: {connected_clients[ws]['audio_route']}]")

                    await ws.send_str(json.dumps({
                        "event": "config_updated",
                        "config": {
                            "archetype": connected_clients[ws]["archetype"],
                            "attitude": connected_clients[ws]["attitude"],
                            "gender": connected_clients[ws]["gender"],
                            "audio_route": connected_clients[ws]["audio_route"],
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

                # Maintain history (max 10 turns for latency and freshness)
                client_state["history"].append({"role": "user", "content": user_text})
                client_state["history"].append({"role": "assistant", "content": reply_text})
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

                # Broadcast completed turn payload to all connected clients
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
                    "audio_route": client_state.get("audio_route", "both"),
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
            ext = "webm"
            if field.filename and "." in field.filename:
                ext = field.filename.rsplit(".", 1)[-1]
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None, groq_engine.transcribe_audio, audio_bytes, f"recording.{ext}"
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
    public_https_url = start_cloudflare_tunnel(SERVER_PORT)
    print_banner(SERVER_HOST, SERVER_PORT, public_https_url)
    app = create_app()
    web.run_app(app, host=SERVER_HOST, port=SERVER_PORT)
