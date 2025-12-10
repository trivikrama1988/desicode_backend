from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, UserProfileUpdate
from app.models.user import User
from app.core.security import get_current_user, hash_password
from app.db.session import get_db

router = APIRouter()

@router.get("/users/profile", response_model=UserResponse, tags=["Users"])
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user

@router.put("/users/profile", response_model=UserResponse, tags=["Users"])
def update_user_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    user = db.query(User).filter(User.id == current_user.id).first()

    # Check if new email is already taken
    if profile_data.email and profile_data.email != user.email:
        existing_user = db.query(User).filter(User.email == profile_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Update fields if provided
    if profile_data.username:
        user.username = profile_data.username
    if profile_data.email:
        user.email = profile_data.email
    if profile_data.password:
        user.password = hash_password(profile_data.password)

    db.commit()
    db.refresh(user)
    return user