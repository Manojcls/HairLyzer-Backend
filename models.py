from sqlalchemy import Boolean, Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    age_range = Column(String)
    gender = Column(String)
    primary_hair_concern = Column(String)
    family_history_hair_loss = Column(Boolean, default=False)
    profile_photo_url = Column(String, nullable=True)
    last_assessment_date = Column(String, nullable=True)
    assessments = relationship("Assessment", back_populates="owner")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    questionnaire = Column(JSON)
    scalp_photo_url = Column(String)
    analysis_results = Column(JSON)
    timestamp = Column(String)

    owner = relationship("User", back_populates="assessments")
