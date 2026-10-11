import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.models_core import User
from ..deps import get_session

router = APIRouter()


@router.post("/users")
def create_user(session: Session = Depends(get_session)):
    user = User(user_id=uuid.uuid4().hex)
    session.add(user)
    session.commit()
    return {"user_id": user.user_id}
