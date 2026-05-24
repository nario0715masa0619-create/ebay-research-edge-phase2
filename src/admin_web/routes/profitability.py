from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.db.models import ProfitabilityScoreModel

router = APIRouter(prefix="/profitability", tags=["profitability"])
templates = Jinja2Templates(directory="src/admin_web/templates")

@router.get("/", response_class=HTMLResponse)
def list_scores(request: Request, db: Session = Depends(get_db)):
    scores = db.query(ProfitabilityScoreModel).order_by(ProfitabilityScoreModel.created_at.desc()).limit(100).all()
    return templates.TemplateResponse(
        "profitability/list.html",
        {"request": request, "scores": scores}
    )

@router.get("/{score_id}", response_class=HTMLResponse)
def view_score(request: Request, score_id: str, db: Session = Depends(get_db)):
    score = db.query(ProfitabilityScoreModel).filter_by(profitability_score_id=score_id).first()
    return templates.TemplateResponse(
        "profitability/detail.html",
        {"request": request, "score": score}
    )
