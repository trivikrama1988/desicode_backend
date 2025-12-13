# app/api/v1/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
from ....schemas.user import UserResponse, UserProfileUpdate
from ....models.user import User
from ...security import get_current_user, hash_password
from ....db.session import get_db

router = APIRouter()


# Consistent response format
class StandardResponse(BaseModel):
    ok: bool = True
    data: Dict[str, Any]


@router.get("/users/profile", response_model=StandardResponse, tags=["Users"])
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return StandardResponse(
        ok=True,
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
            "total_code_executions": current_user.total_code_executions or 0,
            "last_execution_at": current_user.last_execution_at,
            "preferred_language": current_user.preferred_language or "assamese",
            "stripe_customer_id": current_user.stripe_customer_id,
            "razorpay_customer_id": current_user.razorpay_customer_id
        }
    )


@router.put("/users/profile", response_model=StandardResponse, tags=["Users"])
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
            return StandardResponse(
                ok=False,
                data={"error": "Email already registered"}
            )

    # Update fields if provided
    updates = {}
    if profile_data.username:
        user.username = profile_data.username
        updates["username"] = profile_data.username

    if profile_data.email:
        user.email = profile_data.email
        updates["email"] = profile_data.email

    if profile_data.password:
        user.password = hash_password(profile_data.password)
        updates["password_updated"] = True



    db.commit()
    db.refresh(user)

    return StandardResponse(
        ok=True,
        data={
            "message": "Profile updated successfully",
            "updates": updates,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    )