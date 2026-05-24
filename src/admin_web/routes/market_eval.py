from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.db.models import MarketEvaluationResultModel, MarketEvaluationEvidenceModel

router = APIRouter(prefix="/market-eval", tags=["market-eval"])
templates = Jinja2Templates(directory="src/admin_web/templates")

@router.get("/", response_class=HTMLResponse)
def list_evaluations(request: Request, db: Session = Depends(get_db)):
    results = db.query(MarketEvaluationResultModel).order_by(MarketEvaluationResultModel.created_at.desc()).limit(100).all()
    return templates.TemplateResponse(
        "market_eval/list.html",
        {"request": request, "results": results}
    )

@router.get("/{evaluation_id}", response_class=HTMLResponse)
def view_evaluation(request: Request, evaluation_id: str, db: Session = Depends(get_db)):
    result = db.query(MarketEvaluationResultModel).filter_by(market_evaluation_id=evaluation_id).first()
    evidence = None
    if result:
        evidence = db.query(MarketEvaluationEvidenceModel).filter_by(candidate_id=result.candidate_id).order_by(MarketEvaluationEvidenceModel.created_at.desc()).first()
        
    return templates.TemplateResponse(
        "market_eval/detail.html",
        {"request": request, "result": result, "evidence": evidence}
    )
