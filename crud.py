from sqlalchemy.orm import Session
from . import models, schemas, auth
from typing import List

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        username=user.username,
        name=user.name,
        age_range=user.age_range,
        gender=user.gender,
        primary_hair_concern=user.primary_hair_concern,
        family_history_hair_loss=user.family_history_hair_loss,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    db_user = get_user_by_email(db, email=email)
    if not db_user:
        return None
    if not auth.verify_password(password, db_user.hashed_password):
        return None
    return db_user

def create_assessment(db: Session, assessment: schemas.AssessmentCreate, user_id: int):
    db_assessment = models.Assessment(**assessment.dict(), owner_id=user_id)
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

def get_assessments_by_user(db: Session, user_id: int) -> List[models.Assessment]:
    return db.query(models.Assessment).filter(models.Assessment.owner_id == user_id).all()
