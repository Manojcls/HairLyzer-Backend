from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class AssessmentBase(BaseModel):
    questionnaire: Dict[str, Any]
    scalp_photo_url: str
    analysis_results: Dict[str, Any]
    timestamp: str

class AssessmentCreate(AssessmentBase):
    pass

class Assessment(AssessmentBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str
    name: str
    age_range: str
    gender: str
    primary_hair_concern: str
    family_history_hair_loss: bool

class User(UserBase):
    username: str
    email: str
    profile_photo_url: Optional[str] = None
    assessments: List[Assessment] = []

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: str
    password: str
