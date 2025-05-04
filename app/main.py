import os
from json import loads

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import credentials, initialize_app, auth
import uvicorn
import logging
from typing import Dict, Union

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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

# If it's a file path
if os.path.isfile(firebase_json):
    cred = credentials.Certificate(firebase_json)
# If it's a raw JSON string
else:
    cred_dict = loads(firebase_json)
    cred = credentials.Certificate(cred_dict)

initialize_app(cred)


# Injected Login Page with Firebase config
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "firebase_config": FIREBASE_JS_CONFIG}
    )


# Root redirect: handle session or reroute to login
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


# Token-based session login (called by client-side Firebase)
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


# Protected dashboard route
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


# Optional signup admin interface
@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def handle_signup(email: str):
    try:
        user = auth.create_user(email=email)
        return {"message": "Signup successful", "user_id": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        # Parse content
        logging.debug(f"Analyzing content of length: {len(content)}")
        parsed = extract_citations_new(content)
        
        if not parsed:
            logging.warning("Failed to parse content")
            return HTMLResponse(
                "<div class='red f6'>Error: Unable to parse content</div>", 
                status_code=400
            )

        logging.debug(f"Successfully parsed content: {parsed[:100]}...")  # Log first 100 chars
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
            scores: Dict[str, float] = {
                "Word+Position": avg_score(impression_wordpos_count_simple(parsed, n)),
                "Word-only": avg_score(impression_word_count_simple(parsed, n)),
                "Position-only": avg_score(impression_pos_count_simple(parsed, n)),
            }
            logging.debug(f"Calculated scores: {scores}")
        except Exception as e:
            logging.error(f"Error calculating scores: {e}")
            return HTMLResponse(
                "<div class='red f6'>Error calculating scores</div>", 
                status_code=500
            )

        return templates.TemplateResponse(
            "content_doctor.html",
            {
                "request": request,
                "content": content,
                "scores": scores,
            },
        )
    except Exception as e:
        logging.error(f"Unexpected error in analyze route: {e}")
        return HTMLResponse(
            "<div class='red f6'>An unexpected error occurred</div>", 
            status_code=500
        )


# 💻 Local dev command
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
