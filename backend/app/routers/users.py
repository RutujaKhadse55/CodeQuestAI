import uuid

from fastapi import APIRouter

router = APIRouter()


@router.post("/users")
def create_user():
    # TODO [BE] Phase 1: persist in users table once models_core lands.
    return {"user_id": uuid.uuid4().hex}
