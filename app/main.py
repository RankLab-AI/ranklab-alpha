import os
from json import loads
import logging
from app.query_research import run_query_search as execute_search
from app.traffic_predictor import predict_llm_traffic

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import credentials, initialize_app, auth
import uvicorn

# from app.brand_protector import run_brand_analysis, DEFAULT_RISK_KEYWORDS
from app.scoring import compute_scores

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
    # 1) Input validation
    if not content or not content.strip():
        return HTMLResponse(
            "<div class='red f6'>Error: Content cannot be empty</div>", status_code=400
        )
    if len(content) > 50_000:
        return HTMLResponse(
            "<div class='red f6'>Error: Content too long (max 50000 characters)</div>",
            status_code=400,
        )

    # 2) Compute all eight metrics in one go
    try:
        logging.debug(f"Computing GEO metrics for content length {len(content)}")
        scores = compute_scores(content, normalize=False)
        logging.debug(f"Computed scores: {scores}")
    except Exception as e:
        logging.error(f"Error computing scores: {e}")
        return HTMLResponse("<div class='red f6'>Error calculating scores</div>", status_code=500)

    # 3) Render the same template, passing along the full `scores` dict
    return templates.TemplateResponse(
        "content_doctor.html",
        {
            "request": request,
            "content": content,
            "scores": scores,
        },
    )


@app.get("/brand-protector", response_class=HTMLResponse)
async def brand_protector(request: Request):
    return templates.TemplateResponse("brand_protector.html", {"request": request, "results": []})


@app.post("/brand-protector", response_class=HTMLResponse)
async def brand_protector_run(
    request: Request,
    main_brand: str = Form(...),
    competitors: str = Form(""),
    risk_keywords: str = Form(""),
):
    all_brands = [main_brand.strip()] + [c.strip() for c in competitors.split(",") if c.strip()]
    custom_keywords = (
        DEFAULT_RISK_KEYWORDS + [kw.strip().lower() for kw in risk_keywords.split(",")]
        if risk_keywords
        else DEFAULT_RISK_KEYWORDS
    )
    results = [run_brand_analysis(brand, custom_keywords) for brand in all_brands]

    return templates.TemplateResponse(
        "brand_protector.html", {"request": request, "results": results}
    )


@app.get("/query-search", response_class=HTMLResponse)
async def query_search_page(request: Request):
    return templates.TemplateResponse("query_search.html", {"request": request})


@app.post("/query-search", response_class=HTMLResponse)
async def run_query_search(request: Request, topic: str = Form(...)):
    try:
        result = execute_search(topic)
        return templates.TemplateResponse(
            "query_search.html",
            {
                "request": request,
                "topic": result["topic"],
                "queries": result["queries"],
                "results": result["results"],
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "query_search.html", {"request": request, "error": f"Failed to fetch queries: {str(e)}"}
        )


@app.post("/optimize", response_class=HTMLResponse)
async def redirect_to_lab(request: Request, content: str = Form(...)):
    """
    When the user clicks “Optimize Content” we forward them
    to /content-lab with the submitted text.
    """
    return templates.TemplateResponse(
        "content_lab.html",
        {
            "request": request,
            "content": content,
            # no scores here, we’re in the lab phase
        },
    )


@app.get("/traffic-predictor", response_class=HTMLResponse)
async def traffic_form(request: Request):
    """
    Render the empty LLM Traffic Predictor form.
    """
    return templates.TemplateResponse(
        "traffic_predictor.html",
        {"request": request, "result": None, "error": None},
    )


@app.post("/predict-traffic", response_class=HTMLResponse)
async def do_predict(
    request: Request,
    topic: str = Form(...),
    content: str = Form(...),
):
    """
    Accepts topic + content, calls predict_llm_traffic, and re-renders template
    with the resulting data for charts.
    """
    try:
        result = predict_llm_traffic(content=content, topic=topic, num_queries=5)
        return templates.TemplateResponse(
            "traffic_predictor.html",
            {"request": request, "result": result, "error": None},
        )
    except Exception as e:
        # on error, show message
        return templates.TemplateResponse(
            "traffic_predictor.html",
            {"request": request, "result": None, "error": str(e)},
        )


@app.post("/content-lab", response_class=HTMLResponse)
async def content_lab_page(
    request: Request,
    content: str = Form(...),
):
    """
    Dispatch to your optimization logic based on `method`.
    For now, we just echo back with a stub marker.
    """
    # Define available methods here
    available_methods = [
        "Keyword Stuffing",
        "Quotation Addition",
        "Stats Addition",
        "Fluency Optimization",
    ]

    return templates.TemplateResponse(
        "content_lab.html",
        {
            "request": request,
            "content": content,
            "methods": available_methods,
        },
    )


# 💻 Local dev command
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
