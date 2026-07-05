#from fastapi import APIRouter

#router = APIRouter()

#@router.get("/")
#def list_opportunities():
   # return {"message": "Opportunities endpoint - coming soon"}


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityOut, OpportunityCreate
from app.services.scraper import run_all_scrapers

router = APIRouter()

@router.get("/", response_model=List[OpportunityOut])
def list_opportunities(
    category: Optional[str] = None,
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity)
    if category:
        query = query.filter(Opportunity.category == category)
    if search:
        query = query.filter(Opportunity.title.ilike(f"%{search}%"),
                             Opportunity.description.ilike(f"%{search}%"),
                             Opportunity.source.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/{opportunity_id}", response_model=OpportunityOut)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp

@router.post("/", response_model=OpportunityOut)
def create_opportunity(data: OpportunityCreate, db: Session = Depends(get_db)):
    opp = Opportunity(**data.dict())
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

@router.delete("/{opportunity_id}")
def delete_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    db.delete(opp)
    db.commit()
    return {"message": f"Opportunity {opportunity_id} deleted"}

@router.post("/scrape")
def trigger_scrape(db: Session = Depends(get_db)):
    total = run_all_scrapers(db)
    return {"message": f"Scraping complete", "new_opportunities": total}
