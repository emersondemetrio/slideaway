import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_models
from app.routers import auth, decks, rooms
from app.sockets import sio
from app.storage import ensure_bucket

api = FastAPI(title="slideaway-api")

api.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(auth.router)
api.include_router(decks.router)
api.include_router(rooms.router)


@api.on_event("startup")
async def on_startup() -> None:
    await init_models()
    ensure_bucket()


app = socketio.ASGIApp(sio, other_asgi_app=api)
