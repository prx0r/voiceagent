from __future__ import annotations
import os, uuid

# Fish voice foundry adapter. Same contract as edge_tts.synthesize.
# voice = Fish reference_id (cloned owner voice set at onboarding).
# Free lane default (s2.1-pro-free, $0); paid models need API credits.
async def synthesize(text: str, voice: str = "", out_dir="runtime/tts",
                     model: str = "s2.1-pro-free") -> str:
    try:
        from fishaudio import FishAudio
    except ImportError:
        raise RuntimeError("fish-audio-sdk not installed (pip install fish-audio-sdk)")
    key = os.getenv("FISH_API_KEY", "").strip()
    if not key:
        raise RuntimeError("FISH_API_KEY not set")
    voice = voice or os.getenv("FISH_VOICE_ID", "").strip()
    if not voice:
        raise RuntimeError("no voice: pass reference_id or set FISH_VOICE_ID")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{uuid.uuid4().hex}.mp3")
    client = FishAudio(api_key=key)
    try:
        audio = client.tts.convert(text=text, reference_id=voice,
                                   format="mp3", model=model)
    finally:
        client.close()
    with open(path, "wb") as f:
        f.write(audio)
    return path
