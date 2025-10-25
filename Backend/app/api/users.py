from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from app.models.user_model import User
from app.db.database import SessionLocal

router = APIRouter(tags=["users"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateUserRequest(BaseModel):
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    phone: str = Field(..., description="User's phone number")
    gender: str = Field(..., description="User's gender ('M', 'W')")
    orientation: str = Field(..., description="User's sexual orientation ('straight', 'gay', 'lesbian', 'bi')")
    age: int = Field(..., gt=17, lt=100, description="User's age (18-99)")
    accept_non_straight: bool = Field(default=True, description="Accept matches with non-straight partners")
    age_preference: Optional[int] = Field(default=0, description="1 for higher/same, 0 for no preference, -1 for lower/same")


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
async def create_user(user_data: CreateUserRequest, db: Session = Depends(get_db)):
   
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        gender=user_data.gender,
        orientation=user_data.orientation.lower(),
        age=user_data.age,
        accept_non_straight=user_data.accept_non_straight,
        agePreference=user_data.age_preference
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user by their ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        db.delete(user)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
