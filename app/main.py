import os
from json import loads
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import credentials, initialize_app, auth
import uvicorn

from app.utils import (
    verify_firebase_token,
    FIREBASE_JS_CONFIG,
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


# 💻 Local dev command
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
