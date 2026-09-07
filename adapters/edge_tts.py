from __future__ import annotations
import os, uuid

async def synthesize(text: str, voice: str, out_dir="runtime/tts") -> str:
    import edge_tts
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{uuid.uuid4().hex}.mp3")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)
    return path
