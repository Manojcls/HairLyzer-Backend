from fastapi import Depends, FastAPI, HTTPException, File, UploadFile, Form, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import crud, models, schemas, auth
from .database import SessionLocal, engine
import os
import shutil
from typing import List, Optional
from datetime import datetime, timedelta
import random
import random
from pydantic import BaseModel
from jose import JWTError, jwt

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
router = APIRouter()

# Create the 'profile_photos' directory if it doesn't exist
if not os.path.exists("profile_photos"):
    os.makedirs("profile_photos")

# Mount the 'profile_photos' directory to serve static files
app.mount("/profile_photos", StaticFiles(directory="profile_photos"), name="profile_photos")

# Mount the 'scalp_photos' directory to serve static files
app.mount("/scalp_photos", StaticFiles(directory="scalp_photos"), name="scalp_photos")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# Models for the Home Page
class HomeButton(BaseModel):
    text: str
    style: str  # 'primary' or 'secondary'
    action: str


class HairCareTip(BaseModel):
    icon: str
    title: str
    description: str


class NavItem(BaseModel):
    name: str
    icon: str
    is_active: bool


class HomePageResponse(BaseModel):
    greeting: str
    buttons: List[HomeButton]
    tips: List[HairCareTip]
    navigation: List[NavItem]


class ProfileResponse(BaseModel):
    name: str
    email: str
    profile_photo_url: Optional[str] = None
    assessments_count: int
    last_assessment_date: Optional[str] = None
    assessments: List[schemas.Assessment]
    current_hair_health_score: Optional[int] = None



class Questionnaire(BaseModel):
    hair_issue_duration: str
    main_hair_concern: str
    other_hair_concern: Optional[str] = None
    scalp_condition: str
    family_hair_loss_history: str
    diet: str
    hair_wash_frequency: str
    hair_treatments: List[str]
    stress_level: str
    recent_life_changes: List[str]
    medications: str
    hair_loss_stage: str


class ScalpAnalysisResult(BaseModel):
    estimated_hair_density: str
    scalp_redness_level: str
    dandruff_flakes_visible: str
    oilyness_level: str


class TestReport(BaseModel):
    severity: str
    key_findings: List[str]
    diagnosis: str
    recommendations: List[str]
    score: int

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/home")
def get_home_page():
    """
    Returns the data for the mobile app's home page.
    """
    
    buttons = [
        HomeButton(text="Start New Assessment", style="primary", action="/assessment/new"),
        HomeButton(text="View Progress", style="secondary", action="/progress"),
    ]
    tips = [
        HairCareTip(
            icon="brush_icon",
            title="Gentle Brushing",
            description="Use a wide-tooth comb to prevent breakage.",
        ),
        HairCareTip(
            icon="shampoo_icon",
            title="Right Shampoo",
            description="Choose a shampoo that suits your hair type.",
        ),
        HairCareTip(
            icon="conditioner_icon",
            title="Condition Well",
            description="Apply conditioner to the ends of your hair.",
        ),
    ]
    navigation = [
        NavItem(name="Home", icon="home_icon", is_active=True),
        NavItem(name="Assessment", icon="assessment_icon", is_active=False),
        NavItem(name="Progress", icon="progress_icon", is_active=False),
        NavItem(name="Profile", icon="profile_icon", is_active=False),
    ]
    return {"message": "Welcome to Hairlyzer!"}

@router.post("/register/", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user with profile information.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    created_user = crud.create_user(db=db, user=user)
    return created_user

@router.post("/upload-profile-photo/")
async def upload_profile_photo(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Uploads a profile photo for a user.
    """
    file_path = f"profile_photos/{current_user.email}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    url_path = f"/{file_path}"
    current_user.profile_photo_url = url_path
    db.commit()
    return {"message": "Profile photo uploaded successfully", "file_path": url_path}

@router.get("/profile/", response_model=ProfileResponse)
def get_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the user's profile information.
    """
    assessments = crud.get_assessments_by_user(db, user_id=current_user.id)
    assessments_count = len(assessments)
    last_assessment_date = current_user.last_assessment_date
    current_hair_health_score = None
    if assessments:
        latest_assessment = assessments[-1]
        if latest_assessment.analysis_results and isinstance(latest_assessment.analysis_results, dict):
            current_hair_health_score = latest_assessment.analysis_results.get("score")

    return ProfileResponse(
        name=current_user.name,
        email=current_user.email,
        profile_photo_url=current_user.profile_photo_url,
        assessments_count=assessments_count,
        last_assessment_date=last_assessment_date,
        assessments=assessments,
        current_hair_health_score=current_hair_health_score,
    )

@router.post("/assessment/")
async def create_assessment(
    file: UploadFile = File(...),
    questionnaire_str: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new assessment, including a scalp photo and questionnaire.
    """
    # Save the scalp photo
    file_path = f"scalp_photos/{current_user.email}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    scalp_photo_url = f"/{file_path}"

    # Parse the questionnaire
    import json
    questionnaire = json.loads(questionnaire_str)

    # Perform the analysis
    analysis_results = _generate_test_report(questionnaire)

    # Create the assessment
    assessment = schemas.AssessmentCreate(
        questionnaire=questionnaire,
        scalp_photo_url=scalp_photo_url,
        analysis_results=analysis_results.dict(),
        timestamp=datetime.now().isoformat(),
    )
    crud.create_assessment(db=db, assessment=assessment, user_id=current_user.id)

    return {"message": "Assessment created successfully", "analysis": analysis_results}





def _generate_test_report(questionnaire: dict) -> TestReport:
    """
    Generates a test report based on the questionnaire with added randomization.
    """
    answers = questionnaire.get("answers", {})
    
    # --- Dynamic Score ---
    score = random.randint(30, 80)

    # --- Expanded Key Findings Pool ---
    possible_key_findings = [
        "Noticeable thinning in the crown area.",
        "The scalp appears to be in good condition, with no visible irritation.",
        "Some dryness and flakiness is visible on the scalp.",
        "Hair appears to be well-hydrated and has good elasticity.",
        "A moderate amount of dandruff flakes were observed across the scalp.",
        "No significant inflammation or redness was detected.",
        "Hair follicles appear open and are not clogged.",
        "The hair seems brittle and prone to breakage.",
        "Scalp oiliness is within a normal range."
    ]
    key_findings = random.sample(possible_key_findings, k=random.randint(2, 4))

    # Add specific findings based on answers
    if answers.get('scalp_condition') == "Itchy or flaky":
        key_findings.append("The scalp is reported as Itchy or flaky, which may be a contributing factor to hair health.")
    if answers.get('stress_level') in ["Very stressed", "Moderately stressed"]:
        key_findings.append(f"Reported stress level is {answers.get('stress_level')}, which can impact hair health.")

    # --- Dynamic Diagnosis ---
    diagnosis = "General hair health analysis."
    if answers.get("family_hair_loss_history") == "Yes":
        diagnosis = "Potential for Androgenetic Alopecia based on family history."
    elif "hair loss" in answers.get("main_hair_concern", "").lower():
        diagnosis = "Telogen Effluvium (stress-related shedding) is a possibility based on your concerns."

    # --- Expanded Recommendations Pool ---
    possible_recommendations = [
        "Ensure a diet rich in iron, zinc, and B-vitamins to support hair growth.",
        "Incorporate regular scalp massages to improve blood circulation to the follicles.",
        "Avoid harsh chemical treatments and excessive heat styling for a few weeks.",
        "Switch to a gentle, sulfate-free shampoo to avoid stripping natural oils.",
        "Consider using a silk or satin pillowcase to reduce hair friction and breakage overnight.",
        "Stay hydrated by drinking an adequate amount of water throughout the day.",
        "Look into mindfulness or meditation to help manage stress levels.",
        "A weekly deep conditioning treatment could improve hair moisture."
    ]
    recommendations = random.sample(possible_recommendations, k=random.randint(2, 3))

    # Add specific recommendations based on answers
    if "hair loss" in answers.get("main_hair_concern", "").lower():
        recommendations.append("For hair loss concerns, consider a topical minoxidil treatment after consulting a specialist.")
    if answers.get("diet") == "Poor (skips meals, low nutrients)":
        recommendations.append("Your diet may be impacting your hair. Consulting a nutritionist for a personalized plan is highly recommended.")

    # --- Determine Severity based on Score ---
    severity = "Mild"
    if score < 50:
        severity = "Severe"
    elif score < 70:
        severity = "Moderate"

    return TestReport(
        severity=severity,
        key_findings=list(set(key_findings)),  # Ensure unique findings
        diagnosis=diagnosis,
        recommendations=list(set(recommendations)), # Ensure unique recommendations
        score=score,
    )



@router.post("/analyze-scalp/")
async def analyze_scalp(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"message": "Scalp analysis completed successfully", "analysis": {}}

@router.get("/holistic-report/")
def get_holistic_report(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=current_user.email)
    if not user or not user.assessments:
        raise HTTPException(status_code=400, detail="Questionnaire or scalp analysis not completed")
    return {"summary": "summary", "recommendations": []}

@router.get("/test-report/")
def get_test_report(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=current_user.email)
    if not user or not user.assessments:
        raise HTTPException(status_code=400, detail="Questionnaire or scalp analysis not completed")
    return {"report_id": "report_id", "severity": "severity", "key_findings": [], "diagnosis": "diagnosis", "recommendations": []}

@router.get("/progress-tracker/")
def get_progress_tracker(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=current_user.email)
    if not user or len(user.assessments) < 2:
        raise HTTPException(status_code=404, detail="Not enough data to track progress. Complete at least two assessments.")

    # Get the last two assessments
    latest_assessment = user.assessments[-1]
    previous_assessment = user.assessments[-2]

    latest_score = latest_assessment.analysis_results.get("score", 0)
    previous_score = previous_assessment.analysis_results.get("score", 0)

    progress_status = "none"
    suggestions = []

    if latest_score > previous_score:
        progress_status = "good"
        suggestions.append("Your hair health is showing improvement! Keep up with your current routine.")
        suggestions.append("Consistency is key. Continue to follow the recommendations from your last report.")
    else:
        progress_status = "weak"
        suggestions.append("Your hair health has declined or not improved. It might be time to adjust your routine.")
        suggestions.append("Re-evaluate your stress levels and diet, as they are major factors.")
        suggestions.append("Consider consulting a dermatologist for a more in-depth analysis.")

    return {
        "latest_assessment": {"score": latest_score, "timestamp": latest_assessment.timestamp},
        "previous_assessment": {"score": previous_score, "timestamp": previous_assessment.timestamp},
        "progress_status": progress_status,
        "suggestions": suggestions,
    }

@router.get("/profile/{email}")
def get_profile(email: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    assessments = crud.get_assessments_by_user(db, user_id=user.id)
    assessments_count = len(assessments)
    last_assessment_date = user.last_assessment_date

    return ProfileResponse(
        name=user.name,
        email=user.email,
        profile_photo_url=user.profile_photo_url,
        assessments_count=assessments_count,
        last_assessment_date=last_assessment_date,
        assessments=assessments,
    )

@router.get("/settings/{email}")
def get_settings(email: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"message": f"Settings for {email}"}

@router.get("/account-security/{email}")
def get_account_security(email: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"message": f"Account security for {email}"}

@router.post("/questionnaire/")
def submit_questionnaire(questionnaire: Questionnaire, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"message": "Questionnaire submitted successfully"}

@router.post("/logout/")
def logout_user():
    """
    Logs out the user. In a real application, this would invalidate a token.
    """
    return {"message": "Logout successful"}

@router.get("/settings/")
def get_settings(current_user: models.User = Depends(get_current_user)):
    """
    Returns user settings (placeholder).
    """
    return {"message": f"Settings for {current_user.email}"}

@router.get("/account-security/")
def get_account_security(current_user: models.User = Depends(get_current_user)):
    """
    Returns account security information (placeholder).
    """
    return {"message": f"Account security for {current_user.email}"}

@router.get("/help-support/")
def get_help_support():
    """
    Returns help and support information (placeholder).
    """
    return {"message": "For help and support, please visit our website or contact us at support@hairilyzer.com"}

@router.get("/users/", response_model=List[schemas.User])
def get_users(db: Session = Depends(get_db)):
    """
    Returns a list of all registered users (for debugging purposes).
    """
    users = db.query(models.User).all()
    return users

@router.post("/login/", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def get_status():
    """
    Returns the status of the API.
    """
    return {"status": "ok"}

app.include_router(router)
