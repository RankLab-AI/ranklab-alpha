It looks like there are some redundant and unnecessary parts of code in your `main.py`. Here's a breakdown of what can be removed or cleaned up:

1. **Duplicate FastAPI initialization**: You initialize the FastAPI app and mount the static folder twice. This can be removed.

2. **Duplicate logging configuration**: The logging setup is done twice, which can also be cleaned up.

3. **Firebase initialization block**: The Firebase initialization is repeated at the bottom of the code, and there is redundant code with respect to the mock configuration.

4. **Unnecessary imports**: There are some imports that may be unnecessary for your current functionality (e.g., `Dict`, `Union`), depending on the actual usage.

Let’s proceed with the following steps:

### 1. **Remove Duplicate FastAPI Initialization and Static Mounting**

You already have the FastAPI initialization and static files mounting done at the beginning, so the second block of code that repeats these can be removed.

### 2. **Remove Duplicate Logging Configuration**

There’s a second `logging.basicConfig` call. Keep only one, and remove the redundant one.

### 3. **Simplify Firebase Initialization**

Firebase initialization can be simplified by removing the duplicate block at the bottom. You already initialize Firebase at the top, and the second block seems unnecessary. Keep only the Firebase setup with the mock fallback.

### 4. **Remove Unused Imports**

The imports `Dict` and `Union` from `typing` are not being used anywhere in the code. You can safely remove them unless you plan to use them in the future.

---

Here’s the cleaned-up version of your `main.py`:

```python
import os
from json import loads
import logging

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import credentials, initialize_app, auth
import uvicorn

from app.metrics import (
    impression_wordpos_count_simple,
    impression_word_count_simple,
    impression_pos_count_simple,
)
from app.scoring import extract_citations_new
from app.utils import (
    verify_firebase_token,
    FIREBASE_JS_CONFIG,
)

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Firebase initialization
mock_config = {
    "type": "service_account",
    "project_id": "mock-project",
    "private_key_id": "mock-key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEpAIBAAKCAQEAwJENcRev+eXZKvhhWLiV3Lz2MvO+naQRHo59g3vaNQnbgyduN/L4krlr\nJ5c6FiikXdtJNb/QrsAHSyJWCu8j3T9CruiwbidGAk2W0RuViTVspjHUTsIHExx9euWM0Uom\nGvYkoqXahdhPL/zViVSJt+Rt8bHLsMvpb8RquTIb9iKY3SMV2tCofNmyCSgVbghq/y7lKORt\nV/IRguWs6R22fbkb0r2MCYoNAbZ9dqnbRIFNZBC7itYtUoTEresRWcyFMh0zfAh0Ahf6NkwS\nxxcCAwEAAQKCAQBxvipJENcZNqgf+sOvHTA3XTknUMqBanV4V5dU9uV6feVe4lc+/QEKfi9P\nYVwE09s4U/EnhpBa1Fn916zsPeEH3WR8RYgKUDsqYeKhCh7XZ7iQgoVaHDmZVMYL3iqHnmW/\nK2enGNl3sA3Z4oC6eDtfDtVN\n-----END PRIVATE KEY-----\n",
    "client_email": "mock@mock-project.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mock@mock-project.iam.gserviceaccount.com"
}

try:
    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if firebase_json and os.path.isfile(firebase_json):
        logger.info("Using Firebase configuration from file")
        cred = credentials.Certificate(firebase_json)
    elif firebase_json:
        logger.info("Using Firebase configuration from environment variable")
        cred_dict = loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
    else:
        logger.warning("No Firebase configuration found, using mock configuration")
        cred = credentials.Certificate(mock_config)
    
    initialize_app(cred)
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Firebase: {e}")
    logger.warning("Using mock configuration as fallback")
    cred = credentials.Certificate(mock_config)
    initialize_app(cred)

# Routes

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "firebase_config": FIREBASE_JS_CONFIG}
    )

@app.get("/", response_class=RedirectResponse)
async def read_root(request: Request):
    id_token = request.cookies.get("firebase_id_token")
    if not id_token:
        return RedirectResponse(url="/login")
    try:
        usr_attrs = verify_firebase_token(id_token)
    except Exception:
        return RedirectResponse(url="/login")
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(key="user_id", value=usr_attrs["uid"], httponly=True, secure=True)
    response.set_cookie(key="email", value=usr_attrs.get("email"), httponly=True)
    return response

@app.post("/session-login")
async def session_login(request: Request):
    body = await request.json()
    id_token = body.get("idToken")
    if not id_token:
        return JSONResponse({"error": "Missing ID token"}, status_code=400)

    try:
        decoded_token = verify_firebase_token(id_token)
        email = decoded_token.get("email")
        uid = decoded_token.get("uid")
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="firebase_id_token", value=id_token, httponly=True, secure=True)
        response.set_cookie(key="user_id", value=uid, httponly=True, secure=True)
        response.set_cookie(key="email", value=email, httponly=True)
        return response
    except Exception as e:
        print(f"Error verifying token: {e}")
        return JSONResponse({"error": "Invalid ID token"}, status_code=403)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    id_token = request.cookies.get("firebase_id_token")
    if not id_token:
        return RedirectResponse(url="/login")
    try:
        user = verify_firebase_token(id_token)
    except Exception:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.post("/login")
async def login(email: str, password: str):
    raise HTTPException(status_code=400, detail="Use Firebase client SDK on frontend for login.")

@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("firebase_id_token")
    response.delete_cookie("user_id")
    response.delete_cookie("email")
    return response

@app.get("/content-doctor", response_class=HTMLResponse)
def content_doctor_page(request: Request):
    return templates.TemplateResponse("content_doctor.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, content: str = Form(...)):
    # Input validation
    if not content or len(content.strip()) == 0:
        return HTMLResponse(
            "<div class='red f6'>Error: Content cannot be empty</div>", 
            status_code=400
        )
    
    if len(content) > 50000:  # Example max length
        return HTMLResponse(
            "<div class='red f6'>Error: Content too long (max 50000 characters)</div>", 
            status_code=400
        )

    try:
        parsed = extract_citations_new(content)
        if not parsed:
            return HTMLResponse(
                "<div class='red f6'>Error: Unable to parse content</div>", 
                status_code=400
            )

        n = 5

        def avg_score(raw: Union[list, tuple]) -> float:
            """Calculate average score with proper validation"""
            if not isinstance(raw, (list, tuple)):
                logging.warning(f"Invalid type for avg_score: {type(raw)}")
                return 0.0
            if not raw:
                logging.warning("Empty input for avg_score")
                return 0.0
            try:
                return round(sum(raw) / len(raw) * 100, 2)
            except (TypeError, ValueError) as e:
                logging.error(f"Error calculating average score: {e}")
                return 0.0

        # Calculate scores with error handling
        try:
            scores = {
                "Word+Position": avg_score(impression_wordpos_count_simple(parsed, n)),
                "Word-only": avg_score(impression_word_count_simple(parsed, n)),
                "Position-only": avg_score(impression_pos_count_simple(parsed, n)),
            }
        except Exception as e:
            logging.error(f"Error calculating scores: {e}")
            return HTMLResponse(
                "<div class='red f6'>Error calculating scores</div>", 
                status_code=500
            )

        return templates.TemplateResponse(
            "content_doctor.html",
```
