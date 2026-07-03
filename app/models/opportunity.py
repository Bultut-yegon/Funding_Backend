from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.database import Base

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    source = Column(String)
    deadline = Column(DateTime, nullable=True)
    url = Column(String)
