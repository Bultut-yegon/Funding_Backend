#from fastapi import APIRouter

#router = APIRouter()

#@router.get("/")
#def get_notifications():
    #return {"message": "Notifications endpoint - coming soon"}


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.notification import Notification
from fastapi import BackgroundTasks
from app.services.notification_service import notify_users_of_new_opportunities


router = APIRouter()

class NotificationOut:
    pass

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationOut(BaseModel):
    id: int
    message: str
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.get("/", response_model=List[NotificationOut])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.sent_at.desc())
        .limit(20)
        .all()
    )

@router.post("/send")
async def send_notifications(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    background_tasks.add_task(notify_users_of_new_opportunities, db)
    return {"message": "Notifications are being sent in the background"}