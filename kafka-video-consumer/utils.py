# utils.py
import re
import uuid
import time
import os
from urllib.parse import urlparse
from pydantic import BaseModel, HttpUrl, ValidationError, validator
from typing import Optional

FIREBASE_DOMAINS = [
    "firebasestorage.googleapis.com",
    "storage.googleapis.com",
    # agrega tus dominios personalizados si aplica
]

VIDEO_URL_REGEX = re.compile(r"(https?://[^\s]+)")

class VideoMessage(BaseModel):
    video_url: HttpUrl
    metadata: Optional[dict] = {}
    message_id: Optional[str] = None  # UUID if no client id provided
    produced_at: float | None = None  # epoch ms

    @validator("produced_at", pre=True, always=True)
    def set_produced_at(cls, v):
        return v or time.time()

    @validator("message_id", pre=True, always=True)
    def set_message_id(cls, v):
        return v or str(uuid.uuid4())

def extract_video_id_from_url(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
        host = parsed.netloc
        if host in FIREBASE_DOMAINS or "firebase" in host or "storage" in host:
            # ejemplo de path: /v0/b/<bucket>/o/<path>?alt=media&token=...
            # usa path + query mínimamente
            return parsed.path.strip("/").replace("/", "_")
        # fallback: hostname + path
        return f"{host}{parsed.path}".replace("/", "_")
    except Exception:
        return None

def generate_order_key(video_url: str, use_video_id=True):
    """
    Genera key para Kafka:
      - si use_video_id: key = video_id (buen ordering por video)
      - si not: key = global UUID (útil si buscas particionamiento diferente)
    """
    video_id = extract_video_id_from_url(video_url)
    if use_video_id and video_id:
        return video_id.encode("utf-8")
    # fallback: new uuid
    return str(uuid.uuid4()).encode("utf-8")
