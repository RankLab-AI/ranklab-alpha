from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from firebase_admin import initialize_app, auth, firestore
from utils import llm_generate_content, analyze_content

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Initialize Firebase
firebase_credentials = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
}

initialize_app(firebase_credentials)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/signup")
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def handle_signup(email: str):
    try:
        user = auth.create_user(email=email)
        return {"message": "Signup successful", "user_id": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/content-audit")
async def content_audit(request: Request):
    return templates.TemplateResponse("content_audit.html", {"request": request})


@app.post("/analyze-content")
async def analyze_content_endpoint(content: str):
    result = analyze_content(content)
    return JSONResponse(result)


@app.get("/content-generator")
async def content_generator(request: Request):
    return templates.TemplateResponse("content_generator.html", {"request": request})


@app.post("/generate-content")
async def generate_content(topic: str, outline: str, tone: str, language: str):
    generated_content = llm_generate_content(topic, outline, tone, language)
    return JSONResponse({"content": generated_content})


@app.get("/query-search")
async def query_search(request: Request):
    return templates.TemplateResponse("query_search.html", {"request": request})


@app.post("/search-queries")
async def search_queries(keyword: str):
    # Example logic: Fetch related queries from an API or database
    related_queries = [
        {"long_keyword": "how to start a successful blog from scratch"},
        {"long_keyword": "step by step guide to creating a blog"},
    ]
    return JSONResponse(related_queries)


@app.get("/competitor-analysis")
async def competitor_analysis(request: Request):
    return templates.TemplateResponse("competitor_analysis.html", {"request": request})


@app.post("/login")
async def login(email: str, password: str):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return {"message": "Login successful", "user_id": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
