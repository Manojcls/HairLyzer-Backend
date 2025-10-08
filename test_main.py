
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from .main import app, engine
from . import models
import io
import os
def register_and_login(email, password):
    client.post(
        "/register/",
        json={
            "username": email,
            "email": email,
            "password": password,
            "name": "Test User",
            "age_range": "18-40",
            "gender": "Male",
            "primary_hair_concern": "Hair loss",
            "family_history_hair_loss": True,
        },
    )
    response = client.post(
        "/login/",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]



client = TestClient(app)

# NOTE: The tests below are outdated and will likely fail.
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Clear the database before each test
    with Session(engine) as session:
        for table in reversed(models.Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    yield
    # Clear the database after each test
    with Session(engine) as session:
        for table in reversed(models.Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()




def test_get_status():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_home_page():
    response = client.get("/home")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Hairlyzer!"}


def test_register_user():
    response = client.post(
        "/register/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
            "name": "Test User",
            "age_range": "18-40",
            "gender": "Male",
            "primary_hair_concern": "Hair loss",
            "family_history_hair_loss": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"



def test_register_existing_user():
    # First registration
    client.post(
        "/register/",
        json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpassword",
            "name": "Test User 2",
            "age_range": "18-40",
            "gender": "Male",
            "primary_hair_concern": "Hair loss",
            "family_history_hair_loss": True,
        },
    )
    # Second registration with the same email
    response = client.post(
        "/register/",
        json={
            "username": "testuser3",
            "email": "test2@example.com",
            "password": "testpassword",
            "name": "Test User 3",
            "age_range": "18-40",
            "gender": "Male",
            "primary_hair_concern": "Dandruff",
            "family_history_hair_loss": False,
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_login_user():
    # First, register a user
    client.post(
        "/register/",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "loginpassword",
            "name": "Login User",
            "age_range": "18-40",
            "gender": "Female",
            "primary_hair_concern": "Dryness",
            "family_history_hair_loss": False,
        },
    )
    # Then, log in
    response = client.post(
        "/login/",
        data={"username": "login@example.com", "password": "loginpassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials():
    response = client.post(
        "/login/",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_get_users():
    response = client.get("/users/")
    assert response.status_code == 200
    # The exact content will depend on the order of tests, so we just check the type
    assert isinstance(response.json(), list)

    def test_submit_questionnaire():
        email = "questionnaire@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
        # Then, submit the questionnaire
        response = client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": "questionnaire@example.com",
                "hair_issue_duration": "3–6 months",
                "main_hair_concern": "Dryness or frizziness",
                "scalp_condition": "Sometimes",
                "family_hair_loss_history": "No",
                "diet": "Balanced (includes proteins, fruits, vegetables)",
                "hair_wash_frequency": "2–3 times per week",
                "hair_treatments": ["None of these"],
                "stress_level": "Moderately stressed",
                "recent_life_changes": ["None of these"],
                "medications": "No",
                "hair_loss_stage": "Stage 1: Slight hair thinning on top of the head",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Questionnaire submitted successfully"}
    def test_submit_questionnaire_user_not_found():
        email = "nonexistent@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": "anotheruser@example.com",
                "hair_issue_duration": "3–6 months",
                "main_hair_concern": "Dryness or frizziness",
                "scalp_condition": "Sometimes",
                "family_hair_loss_history": "No",
                "diet": "Balanced (includes proteins, fruits, vegetables)",
                "hair_wash_frequency": "2–3 times per week",
                "hair_treatments": ["None of these"],
                "stress_level": "Moderately stressed",
                "recent_life_changes": ["None of these"],
                "medications": "No",
                "hair_loss_stage": "Stage 1: Slight hair thinning on top of the head",
            },
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "User not found"}
    def test_analyze_scalp():
        email = "scalpuser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
    
        # Create a dummy image file
        file_content = b"dummy image data"
        file = io.BytesIO(file_content)
    
        response = client.post(
            "/analyze-scalp/",
            headers=headers,
            files={"file": ("test_image.jpg", file, "image/jpeg")},
        )
    
        assert response.status_code == 200
        assert response.json()["message"] == "Scalp analysis completed successfully"
        assert "analysis" in response.json()
    def test_get_holistic_report():
        email = "holisticuser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": email,
                "hair_issue_duration": "3–6 months",
                "main_hair_concern": "Dandruff",
                "scalp_condition": "Yes, often",
                "family_hair_loss_history": "I don’t know",
                "diet": "Poor (skips meals, low nutrients)",
                "hair_wash_frequency": "Daily",
                "hair_treatments": ["None of these"],
                "stress_level": "Very stressed",
                "recent_life_changes": ["Major illness (fever, infection, surgery)"],
                "medications": "Yes",
                "hair_loss_stage": "Stage 2: Moderate thinning, widening part line",
            },
        )
        file_content = b"dummy image data"
        file = io.BytesIO(file_content)
        client.post(
            "/analyze-scalp/",
            headers=headers,
            files={"file": ("test_image.jpg", file, "image/jpeg")},
        )
    
        # Get the holistic report
        response = client.get(f"/holistic-report/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
    def test_get_holistic_report_missing_data():
        email = "missingdatauser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
    
        response = client.get(f"/holistic-report/", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "Questionnaire or scalp analysis not completed"}
    def test_get_test_report():
        email = "testreportuser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": email,
                "hair_issue_duration": "6+ months",
                "main_hair_concern": "Hair loss",
                "scalp_condition": "No",
                "family_hair_loss_history": "Yes",
                "diet": "Balanced (includes proteins, fruits, vegetables)",
                "hair_wash_frequency": "2–3 times per week",
                "hair_treatments": ["None of these"],
                "stress_level": "Low stress",
                "recent_life_changes": ["None of these"],
                "medications": "No",
                "hair_loss_stage": "Stage 3: Significant thinning, visible scalp",
            },
        )
        file_content = b"dummy image data"
        file = io.BytesIO(file_content)
        client.post(
            "/analyze-scalp/",
            headers=headers,
            files={"file": ("test_image.jpg", file, "image/jpeg")},
        )
    
        # Get the test report
        response = client.get(f"/test-report/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data
        assert "severity" in data
        assert "key_findings" in data
        assert "diagnosis" in data
        assert "recommendations" in data
        assert isinstance(data["key_findings"], list)
        assert isinstance(data["recommendations"], list)
    def test_get_test_report_missing_data():
        email = "testreportmissingdatauser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
    
        response = client.get(f"/test-report/", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "Questionnaire or scalp analysis not completed"}
    def test_progress_tracker_no_history():
        email = "progress_no_history@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/progress-tracker/", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"progress_summary": "Not enough data to track progress. Complete at least two tests."}
    def test_progress_tracker_one_report():
        email = "progress_one_report@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": email,
                "hair_issue_duration": "3–6 months",
                "main_hair_concern": "Hair loss",
                "scalp_condition": "No",
                "family_hair_loss_history": "Yes",
                "diet": "Balanced",
                "hair_wash_frequency": "2-3 times a week",
                "hair_treatments": ["None"],
                "stress_level": "Low",
                "recent_life_changes": ["None"],
                "medications": "No",
                "hair_loss_stage": "Stage 2",
            },
        )
        client.post(
            "/analyze-scalp/",
            headers=headers,
            files={"file": ("test.jpg", b"test", "image/jpeg")},
        )
        client.get(f"/test-report/", headers=headers)
        response = client.get(f"/progress-tracker/", headers=headers)
        assert response.status_code == 200
        assert response.json()["progress_summary"] == "Not enough data to track progress. Complete at least two tests."
    def test_progress_tracker_improvement():
        email = "progress_improvement@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}

        # First report (Severe)
        client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": email,
                "hair_issue_duration": "3–6 months",
                "main_hair_concern": "Hair loss",
                "scalp_condition": "No",
                "family_hair_loss_history": "Yes",
                "diet": "Balanced",
                "hair_wash_frequency": "2-3 times a week",
                "hair_treatments": ["None"],
                "stress_level": "Low",
                "recent_life_changes": ["None"],
                "medications": "No",
                "hair_loss_stage": "Stage 2",
            },
        )
        client.get(f"/test-report/", headers=headers)

        # Second report (Mild)
        client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": email,
                "hair_issue_duration": "3–6 months",
                "main_hair_concern": "Hair loss",
                "scalp_condition": "No",
                "family_hair_loss_history": "Yes",
                "diet": "Balanced",
                "hair_wash_frequency": "2-3 times a week",
                "hair_treatments": ["None"],
                "stress_level": "Low",
                "recent_life_changes": ["None"],
                "medications": "No",
                "hair_loss_stage": "Stage 2",
            },
        )
        client.get(f"/test-report/", headers=headers)

        response = client.get(f"/progress-tracker/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["progress_summary"] == "Your hair health is showing improvement. Keep up the good work!"
def test_upload_profile_photo():
    email = "photouser@example.com"
    client.post(
        "/register/",
        json={
            "username": "photouser",
            "email": email,
            "password": "password",
            "name": "Photo User",
            "age_range": "20-30",
            "gender": "Female",
            "primary_hair_concern": "Split ends",
            "family_history_hair_loss": False,
        },
    )

    response = client.post(
        "/login/",
        data={"username": email, "password": "password"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_content = b"my photo data"
    file = io.BytesIO(file_content)

    response = client.post(
        "/upload-profile-photo/",
        data={"email": email},
        files={"file": ("photo.jpg", file, "image/jpeg")},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Profile photo uploaded successfully"
    assert data["file_path"] == f"/profile_photos/{email}_photo.jpg"
    
    # Verify the file was saved
    assert os.path.exists(f"profile_photos/{email}_photo.jpg")

    def test_get_profile():
        email = "profileuser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/questionnaire/",
            headers=headers,
            json={
                "email": email,
                "hair_issue_duration": "3–6 months",
                "main_hair_concern": "Hair loss",
                "scalp_condition": "No",
                "family_hair_loss_history": "Yes",
                "diet": "Balanced",
                "hair_wash_frequency": "2-3 times a week",
                "hair_treatments": ["None"],
                "stress_level": "Low",
                "recent_life_changes": ["None"],
                "medications": "No",
                "hair_loss_stage": "Stage 2",
            },
        )
        client.post(
            "/analyze-scalp/",
            headers=headers,
            files={"file": ("test.jpg", b"test", "image/jpeg")},
        )
        client.get(f"/test-report/", headers=headers)
    
        response = client.get(f"/profile/{email}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test User"
        assert data["email"] == email
        assert data["assessments_count"] == 1
        assert data["last_assessment_date"] is not None
        assert len(data["assessment_history"]) == 1
def test_logout():
    response = client.post("/logout/")
    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful"}

    def test_get_settings():
        email = "settingsuser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/settings/{email}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": f"Settings for {email}"}
    def test_get_account_security():
        email = "securityuser@example.com"
        password = "testpassword"
        token = register_and_login(email, password)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/account-security/{email}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": f"Account security for {email}"}
def test_get_help_support():
    response = client.get("/help-support/")
    assert response.status_code == 200
    assert "support@hairilyzer.com" in response.json()["message"]
