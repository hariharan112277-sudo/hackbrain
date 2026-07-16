from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Unique user authentication identifier email account")
    full_name: str = Field(..., min_length=2, max_length=50, description="Legal full name designation")

class UserCreate(UserBase):
    password: str = Field(..., min_length=12, description="Plaintext password matching Stage-5 minimum length specifications")

class UserResponse(UserBase):
    id: int = Field(..., description="Unique database surrogate integer key identifier")
    is_active: bool = Field(True, description="Flag indicating if the user profile account status is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp documenting instance generation time")

    class Config:
        from_attributes = True
