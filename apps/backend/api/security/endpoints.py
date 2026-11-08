from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...db_models import AuthToken, User
from ...models import DEFAULT_PROBLEM_ID, ProblemId
from .models import SignInRequest, SignInResponse
from .security import check_signin_rate_limit, hash_password, verify_password

router = APIRouter()

@router.post("/api/auth/signin", response_model=SignInResponse, status_code=200)
def sign_in(payload: SignInRequest, db: Session = Depends(get_db)) -> SignInResponse:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Please provide a valid email address")

    check_signin_rate_limit(email)

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            last_problem_id=DEFAULT_PROBLEM_ID,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = str(uuid4())
    db.add(AuthToken(token=token, user_id=user.id))
    db.commit()

    return SignInResponse(token=token, email=user.email, lastProblemId=ProblemId(user.last_problem_id))

@router.delete("/api/auth/signout", status_code=204)
def sign_out(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> None:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        auth_token = db.get(AuthToken, token)
        if auth_token:
            db.delete(auth_token)
            db.commit()
    return None