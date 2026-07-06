from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.database import get_db
from app.core.security import get_admin_user
from app.models.user import User
from app.models.opportunity import Opportunity
from app.models.bookmark import Bookmark
from app.models.notification import Notification
from app.schemas.opportunity import OpportunityOut, OpportunityCreate
from app.schemas.user import UserOut

router = APIRouter()

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    total_users = db.query(User).count()
    total_opportunities = db.query(Opportunity).count()
    total_bookmarks = db.query(Bookmark).count()
    total_notifications = db.query(Notification).count()

    categories = db.query(
        Opportunity.category,
        func.count(Opportunity.id).label("count")
    ).group_by(Opportunity.category).all()

    return {
        "total_users": total_users,
        "total_opportunities": total_opportunities,
        "total_bookmarks": total_bookmarks,
        "total_notifications": total_notifications,
        "opportunities_by_category": [
            {"category": c, "count": n} for c, n in categories
        ],
    }

@router.get("/users", response_model=List[UserOut])
def get_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    return db.query(User).all()

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}

@router.get("/opportunities", response_model=List[OpportunityOut])
def get_all_opportunities(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    return db.query(Opportunity).all()

@router.post("/opportunities", response_model=OpportunityOut)
def create_opportunity(
    data: OpportunityCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    opp = Opportunity(**data.dict())
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

@router.delete("/opportunities/{opportunity_id}")
def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    db.delete(opp)
    db.commit()
    return {"message": f"Opportunity {opportunity_id} deleted"}

@router.post("/scrape")
def trigger_scrape(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    from app.services.scraper import run_all_scrapers
    total = run_all_scrapers(db)
    return {"message": "Scraping complete", "new_opportunities": total}
