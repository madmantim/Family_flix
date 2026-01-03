from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from PIL import Image
from io import BytesIO
import os
import logging
from ..database import get_db
from ..models import Member
from ..schemas import MemberCreate, MemberResponse, MemberUpdate

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
AVATAR_SIZE = 256
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter()


@router.get("/", response_model=List[MemberResponse])
def get_members(db: Session = Depends(get_db)):
    """Get all family members"""
    return db.query(Member).all()


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    """Get a specific member"""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.post("/", response_model=MemberResponse, status_code=201)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    """Create a new family member"""
    existing = db.query(Member).filter(Member.name == member.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member with this name already exists")

    db_member = Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.patch("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, member: MemberUpdate, db: Session = Depends(get_db)):
    """Update a member"""
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = member.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_member, field, value)

    db.commit()
    db.refresh(db_member)
    return db_member


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """Delete a member"""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()


@router.post("/{member_id}/avatar", response_model=MemberResponse)
async def upload_avatar(
    member_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and set a member's avatar image"""
    # Validate member exists
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a JPEG, PNG, or WebP image."
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 5MB.")

    # Process image with Pillow
    try:
        img = Image.open(BytesIO(content))
        img = img.convert("RGB")  # Ensure RGB for JPEG output

        # Center crop to square
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))

        # Resize to target size
        img = img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)

        # Save to static directory
        static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "avatars")
        os.makedirs(static_dir, exist_ok=True)
        avatar_path = os.path.join(static_dir, f"{member_id}.jpg")
        img.save(avatar_path, "JPEG", quality=85)

    except Exception as e:
        logger.error("Failed to process avatar for member %d: %s", member_id, e)
        raise HTTPException(status_code=400, detail="Failed to process image.")

    # Update member's avatar_url
    member.avatar_url = f"/static/avatars/{member_id}.jpg"
    db.commit()
    db.refresh(member)

    return member
