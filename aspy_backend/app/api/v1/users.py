# app/api/v1/users.py - CORRECTED VERSION
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, UserProfileUpdate
from app.models.user import User  # Import from models, don't define here
from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter(tags=["Users"])

@router.get("/users/profile", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/users/profile", response_model=UserResponse)
def update_user_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if profile_data.email != user.email:
        existing_user = db.query(User).filter(User.email == profile_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    user.username = profile_data.username
    user.email = profile_data.email
    db.commit()
    db.refresh(user)
    return user