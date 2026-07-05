from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.bookmark import Bookmark
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityOut

router = APIRouter()

@router.get("/", response_model=List[OpportunityOut])
def get_bookmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == current_user.id).all()
    opp_ids = [b.opportunity_id for b in bookmarks]
    return db.query(Opportunity).filter(Opportunity.id.in_(opp_ids)).all()

@router.post("/{opportunity_id}")
def add_bookmark(
    opportunity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.opportunity_id == opportunity_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already bookmarked")

    bookmark = Bookmark(user_id=current_user.id, opportunity_id=opportunity_id)
    db.add(bookmark)
    db.commit()
    return {"message": "Bookmarked successfully"}

@router.delete("/{opportunity_id}")
def remove_bookmark(
    opportunity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.opportunity_id == opportunity_id,
    ).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark removed"}
