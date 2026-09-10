from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional
from app.core.auth import AuthUser, get_current_user
from app.models.user_model import User
from app.db.database import get_db

router = APIRouter(tags=["users"])

# The matchmaker keys off these exact values (see matchmaking/helpers.py), and
# the form sends "bisexual", which silently dropped those users from every pool.
ORIENTATIONS = {
    "straight": "straight",
    "gay": "gay",
    "lesbian": "lesbian",
    "bi": "bi",
    "bisexual": "bi",
}


class CreateUserRequest(BaseModel):
    # email is taken from the session, never from the request body.
    name: str = Field(..., description="User's full name")
    phone: str = Field(..., description="User's phone number")
    gender: str = Field(..., description="User's gender ('M', 'W')")
    orientation: str = Field(..., description="User's sexual orientation ('straight', 'gay', 'lesbian', 'bi')")
    age: int = Field(..., gt=16, lt=100, description="User's age (17-99)")
    accept_non_straight: bool = Field(default=True, description="Accept matches with non-straight partners")
    age_preference: Optional[int] = Field(default=0, description="1 for higher/same, 0 for no preference, -1 for lower/same")

    @field_validator("gender")
    @classmethod
    def check_gender(cls, v: str) -> str:
        if v not in ("M", "W"):
            raise ValueError("gender must be 'M' or 'W'")
        return v

    @field_validator("orientation")
    @classmethod
    def check_orientation(cls, v: str) -> str:
        try:
            return ORIENTATIONS[v.strip().lower()]
        except KeyError:
            raise ValueError(f"orientation must be one of {sorted(set(ORIENTATIONS))}")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 10:
            raise ValueError("phone must be 10 digits")
        return digits

    @field_validator("age_preference")
    @classmethod
    def check_age_preference(cls, v: Optional[int]) -> int:
        if v not in (-1, 0, 1, None):
            raise ValueError("age_preference must be -1, 0 or 1")
        return v or 0


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    gender: str
    orientation: str
    age: int
    accept_non_straight: bool
    age_preference: Optional[int]

    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user_data: CreateUserRequest,
    caller: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create the signed-in user's profile.
    """
    email = caller.email

    existing_user = db.query(User).filter(
        (User.email == email) | (User.phone == user_data.phone)
    ).first()

    if existing_user:
        if existing_user.email == email:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        else:
            raise HTTPException(status_code=400, detail="User with this phone number already exists")

    new_user = User(
        name=user_data.name,
        email=email,
        phone=user_data.phone,
        gender=user_data.gender,
        orientation=user_data.orientation,
        age=user_data.age,
        accept_non_straight=user_data.accept_non_straight,
        age_preference=user_data.age_preference
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        # Two tabs, a double tap, or a retry racing the check above.
        db.rollback()
        raise HTTPException(status_code=409, detail="This email or phone is already registered")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/me", response_model=UserResponse)
def get_own_user(
    caller: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == caller.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    caller: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.email != caller.email:
        # Don't confirm whether the id exists; these rows hold phone numbers.
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    caller: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete your own profile.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.email != caller.email:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        db.delete(user)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
