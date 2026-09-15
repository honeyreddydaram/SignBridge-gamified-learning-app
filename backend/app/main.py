from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, interpretation, lessons, quests, recognition, users, vocabulary
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="SignBridge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(lessons.router)
app.include_router(recognition.router)
app.include_router(interpretation.router)
app.include_router(vocabulary.router)
app.include_router(quests.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
