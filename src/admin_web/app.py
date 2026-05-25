import os
import secrets
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional

from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.status_badges import StatusBadgeMapper

app = FastAPI(
    title="eBay Research Edge Admin Web View",
    description="Lightweight SSR FastAPI visual management and operational panel",
    version="0.1"
)

# 1. Static Files and Templates Setup
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Register Jinja2 global functions
templates.env.globals["badge_class_candidate"] = StatusBadgeMapper.get_candidate_class
templates.env.globals["badge_class_readiness"] = StatusBadgeMapper.get_readiness_class
templates.env.globals["badge_class_job"] = StatusBadgeMapper.get_job_class
templates.env.globals["badge_class_notification"] = StatusBadgeMapper.get_notification_class

def merge_query_params(request: Request, **kwargs) -> str:
    params = dict(request.query_params)
    for k, v in kwargs.items():
        if v is None or v == "":
            params.pop(k, None)
        else:
            params[k] = str(v)
    if not params:
        return ""
    import urllib.parse
    return "?" + urllib.parse.urlencode(params)

templates.env.globals["merge_query_params"] = merge_query_params

# 2. Session Middleware for Flash Messages
session_secret = os.environ.get("ADMIN_WEB_SESSION_SECRET", "super-secret-key-1234567890-abcdefg")
app.add_middleware(SessionMiddleware, secret_key=session_secret)

# Helper to add flash messages easily
@app.middleware("http")
async def add_flash_helper(request: Request, call_next):
    def flash(message: str, category: str = "success"):
        if "flash" not in request.session:
            request.session["flash"] = []
        request.session["flash"].append({"message": message, "category": category})
    request.state.flash = flash
    response = await call_next(request)
    return response

# 3. Basic Security / Authentication
security = HTTPBasic(auto_error=False)

def authenticate_user(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    auth_enabled = os.environ.get("ADMIN_WEB_BASIC_AUTH_ENABLED", "false").lower() == "true"
    if not auth_enabled:
        return "anonymous"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    expected_username = os.environ.get("ADMIN_WEB_BASIC_AUTH_USERNAME", "admin")
    expected_password = os.environ.get("ADMIN_WEB_BASIC_AUTH_PASSWORD", "secret123")
    
    is_correct_username = secrets.compare_digest(credentials.username, expected_username)
    is_correct_password = secrets.compare_digest(credentials.password, expected_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 4. Global Root Redirection
@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/admin")

# 5. Route Registry & Imports
# We import routes dynamically to prevent circular dependencies
from src.admin_web.routes.dashboard import router as dashboard_router
from src.admin_web.routes.sellers import router as sellers_router
from src.admin_web.routes.jobs import router as jobs_router
from src.admin_web.routes.candidates import router as candidates_router
from src.admin_web.routes.listings import router as listings_router
from src.admin_web.routes.review import router as review_router
from src.admin_web.routes.discovery_review import router as discovery_review_router
from src.admin_web.routes.notifications import router as notifications_router
from src.admin_web.routes.escalation import router as escalation_router
from src.admin_web.routes.doctor import router as doctor_router
from src.admin_web.routes.execution_history import router as execution_history_router

# Include routers
app.include_router(dashboard_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(sellers_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(jobs_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(candidates_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(listings_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(review_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(discovery_review_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(notifications_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(escalation_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(doctor_router, prefix="/admin", dependencies=[Depends(authenticate_user)])
app.include_router(execution_history_router, prefix="", dependencies=[Depends(authenticate_user)])
