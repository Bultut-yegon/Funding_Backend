from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.bookmark import Bookmark
from app.models.opportunity import Opportunity
from app.schemas.bookmark import BookmarkOut, BookmarkUpdate

router = APIRouter()

VALID_STATUSES = ["Saved", "Applied", "Shortlisted", "Won", "Lost"]

@router.get("/", response_model=List[BookmarkOut])
def get_bookmarks(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Bookmark).options(
        joinedload(Bookmark.opportunity)
    ).filter(Bookmark.user_id == current_user.id)

    if status:
        query = query.filter(Bookmark.status == status)

    return query.order_by(Bookmark.created_at.desc()).all()

@router.post("/{opportunity_id}", response_model=BookmarkOut)
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

    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    bookmark = Bookmark(
        user_id=current_user.id,
        opportunity_id=opportunity_id,
        status="Saved",
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    # reload with relationship
    return db.query(Bookmark).options(
        joinedload(Bookmark.opportunity)
    ).filter(Bookmark.id == bookmark.id).first()

@router.patch("/{opportunity_id}", response_model=BookmarkOut)
def update_bookmark(
    opportunity_id: int,
    data: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.opportunity_id == opportunity_id,
    ).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    if data.status:
        if data.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Status must be one of {VALID_STATUSES}")
        bookmark.status = data.status
        if data.status == "Applied":
            bookmark.applied_date = datetime.utcnow()

    if data.notes is not None:
        bookmark.notes = data.notes

    db.commit()
    db.refresh(bookmark)

    return db.query(Bookmark).options(
        joinedload(Bookmark.opportunity)
    ).filter(Bookmark.id == bookmark.id).first()

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

@router.get("/stats/summary")
def bookmark_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id
    ).all()

    stats = {status: 0 for status in VALID_STATUSES}
    for b in bookmarks:
        if b.status in stats:
            stats[b.status] += 1

    return {"total": len(bookmarks), "by_status": stats}