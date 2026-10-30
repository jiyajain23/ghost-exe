import sqlite3

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.schemas import HealthResponse
from app.config import Settings
from app.ghost.ollama import OllamaGhostAdapter
from app.ghost.adapter import MockGhostAdapter
from app.api.routes import game_routes
from app.director.game import Director, GameError
from app.storage.repository import Repository


def create_app(settings: Settings | None = None, repository: Repository | None = None) -> FastAPI:
    settings = settings or Settings.from_environment()
    application = FastAPI(title='GHOST.EXE', docs_url=None, redoc_url=None, openapi_url=None)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=['http://127.0.0.1:5173', 'http://localhost:5173'],
        allow_methods=['GET', 'POST'],
        allow_headers=['Accept', 'Content-Type'],
    )

    @application.middleware('http')
    async def local_mutations(request: Request, call_next):
        # CORS alone does not block cross-origin simple POST requests.
        if request.method == 'POST':
            origin = request.headers.get('origin')
            if origin is not None and origin not in {'http://127.0.0.1:5173', 'http://localhost:5173'}:
                return JSONResponse({'detail': 'Origin is not permitted.'}, status_code=403)
            if request.headers.get('content-type', '').split(';')[0].strip() != 'application/json':
                return JSONResponse({'detail': 'Use application/json.'}, status_code=415)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @application.exception_handler(GameError)
    async def game_error(request: Request, error: GameError):
        return JSONResponse({'detail': error.message}, status_code=error.status)

    @application.exception_handler(sqlite3.Error)
    @application.exception_handler(OSError)
    async def storage_error(request: Request, error: Exception):
        return JSONResponse({'detail': 'Local save is unavailable. Close other game servers and retry.'}, status_code=503)

    ghost = OllamaGhostAdapter(settings) if settings.agent_mode == 'ollama' else MockGhostAdapter()
    application.include_router(game_routes(Director(repository or Repository(), ghost, timeout=settings.model_timeout_seconds)))

    @application.get('/api/health', response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(agent_mode=settings.agent_mode)

    return application


app = create_app()
