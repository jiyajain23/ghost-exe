from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.schemas import (ChatAction, ChatResponse, FilesResponse, OpenFileAction,
                             OpenFileResponse, PhotoChoiceAction, PhotoResponse,
                             RunResponse, StartRunAction, StartRunResponse)
from app.director.game import Director


def game_routes(director: Director) -> APIRouter:
    router = APIRouter(prefix='/api')

    @router.get('/runs', include_in_schema=False)
    def no_run_listing():
        # Preserve the private boundary: no endpoint enumerates saved run IDs.
        raise HTTPException(404, 'Not found')

    @router.post('/runs', response_model=StartRunResponse, status_code=201)
    def start(action: StartRunAction):
        return director.start(action.restart_from_run_id)

    @router.get('/runs/{run_id}', response_model=RunResponse)
    def resume(run_id: UUID):
        return director.resume(run_id)

    @router.get('/runs/{run_id}/files', response_model=FilesResponse)
    def files(run_id: UUID):
        return director.files(run_id)

    @router.post('/runs/{run_id}/open-file', response_model=OpenFileResponse)
    def open_file(run_id: UUID, action: OpenFileAction):
        return director.open_file(run_id, action.file_id)

    @router.post('/runs/{run_id}/photo-choice', response_model=PhotoResponse)
    def photo(run_id: UUID, action: PhotoChoiceAction):
        return director.photo(run_id, action.choice)

    @router.post('/runs/{run_id}/chat', response_model=ChatResponse)
    async def chat(run_id: UUID, action: ChatAction):
        return await director.chat(run_id, action.message)

    return router
