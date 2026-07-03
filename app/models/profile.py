from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    education_level = Column(String, nullable=True)
    interests = Column(String, nullable=True)   # comma-separated for now
    industry = Column(String, nullable=True)
    country = Column(String, nullable=True)
    skills = Column(String, nullable=True)      # comma-separated for now

    user = relationship("User", backref="profile")
