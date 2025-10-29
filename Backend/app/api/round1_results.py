from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.match_history import MatchHistory, MatchStatus
from pydantic import BaseModel
import json
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

router = APIRouter()

# Configuration - set these via environment variables or config
ROUND1_RESULTS_PUBLISHED = os.getenv("ROUND1_RESULTS_PUBLISHED", "false").lower() == "true"
MATCHES_JSON_PATH = os.getenv("MATCHES_JSON_PATH", "matches_20251029_043722.json")  # Default to latest
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

class MatchResult(BaseModel):
    name: str
    email: str
    phone: str

class Round1ResultResponse(BaseModel):
    status: str  # "not_registered", "match_found", "no_match", "not_published"
    match: Optional[MatchResult] = None
    message: Optional[str] = None
    match_status: Optional[str] = None  # "ACCEPTED", "PENDING", "DECLINED"

class UpdateMatchStatusRequest(BaseModel):
    user_email: str
    apply_round2: bool  # True for PENDING, False for REJECTED

def get_latest_matches_json():
    """Get the path to the latest matches JSON file"""
    backend_dir = Path(__file__).parent.parent.parent
    matches_path = backend_dir / MATCHES_JSON_PATH
    
    if not matches_path.exists():
        # If specified file doesn't exist, try to find the latest one
        all_matches = sorted(backend_dir.glob("matches_*.json"), reverse=True)
        if all_matches:
            return all_matches[0]
        return None
    
    return matches_path

def find_user_match(user_email: str, matches_data: dict):
    """Find a user's match in the matches JSON data"""
    for match in matches_data.get("matches", []):
        user_1 = match.get("user_1", {})
        user_2 = match.get("user_2", {})
        
        if user_1.get("email") == user_email:
            return {
                "name": user_2.get("name"),
                "email": user_2.get("email"),
                "phone": user_2.get("phone")
            }
        elif user_2.get("email") == user_email:
            return {
                "name": user_1.get("name"),
                "email": user_1.get("email"),
                "phone": user_1.get("phone")
            }
    
    return None

@router.get("/check-result", response_model=Round1ResultResponse)
async def check_round1_result(email: str):
    """
    Check Round 1 results for a user
    
    Returns:
    - not_published: Results not published yet
    - not_registered: User not registered
    - match_found: Match found with details
    - no_match: No match found (automatic Round 2)
    """
    
    # Check if results are published
    if not ROUND1_RESULTS_PUBLISHED:
        return Round1ResultResponse(
            status="not_published",
            message="Round 1 results have not been published yet"
        )
    
    # Check if user is registered
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return Round1ResultResponse(
            status="not_registered",
            message="You are not registered. Stay tuned for Round 2!"
        )
    
    # Load matches JSON
    matches_file = get_latest_matches_json()
    if not matches_file:
        raise HTTPException(status_code=500, detail="Matches file not found")
    
    try:
        with open(matches_file, 'r') as f:
            matches_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading matches file: {str(e)}")
    
    # Find user's match
    match = find_user_match(email, matches_data)
    
    # Get user's match status from match_history
    match_history = db.query(MatchHistory).filter(
        MatchHistory.user_id == user.id
    ).first()
    
    # Safely get match status - handle None cases
    user_match_status = None
    if match_history and match_history.status:
        user_match_status = match_history.status.value
    
    if match:
        return Round1ResultResponse(
            status="match_found",
            match=MatchResult(**match),
            message="Congratulations! We found your match!",
            match_status=user_match_status
        )
    else:
        return Round1ResultResponse(
            status="no_match",
            message="You will be automatically enrolled in Round 2!",
            match_status=None  # No status for unmatched users
        )

@router.post("/update-match-status")
async def update_match_status(
    request: UpdateMatchStatusRequest
):
    """
    Update user's match status based on Round 2 decision
    
    - apply_round2=True: Set status to PENDING (Apply Round 2)
    - apply_round2=False: Set status to REJECTED (No Round 2)
    """
    
    # Get user
    user = db.query(User).filter(User.email == request.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update status for this user's match history records
    new_status = MatchStatus.PENDING if request.apply_round2 else MatchStatus.REJECTED
    
    # Update all match history records for this user
    db.query(MatchHistory).filter(
        MatchHistory.user_id == user.id
    ).update({
        "status": new_status
    })
    
    db.commit()
    
    return {
        "success": True,
        "status": new_status.value,
        "message": "Applied for Round 2!" if request.apply_round2 else "Opted out of Round 2"
    }
