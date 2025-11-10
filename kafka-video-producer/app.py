import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from producer import send_video, start_producer, stop_producer

class VideoRequest(BaseModel):
    video_url: str
    metadata: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_producer()
    yield
    await stop_producer()

# ✅ aquí se pasa lifespan al crear la app
app = FastAPI(title="Kafka Producer API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/publish")
async def publish_video(request: VideoRequest):
    try:
        result = await send_video(request.video_url, request.metadata)
        return {
            "status": "ok",
            "topic": result.topic,
            "partition": result.partition,
            "offset": result.offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
