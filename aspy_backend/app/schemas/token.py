from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

    class Config:
        from_attributes = True