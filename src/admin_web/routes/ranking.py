from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.db.models import ListingDecisionModel

router = APIRouter(prefix="/ranking", tags=["ranking"])
templates = Jinja2Templates(directory="src/admin_web/templates")

@router.get("/", response_class=HTMLResponse)
def list_decisions(request: Request, queue: str = None, db: Session = Depends(get_db)):
    query = db.query(ListingDecisionModel)
    if queue:
        query = query.filter_by(queue_type=queue)
    
    decisions = query.order_by(ListingDecisionModel.queue_rank.desc(), ListingDecisionModel.created_at.desc()).limit(100).all()
    
    return templates.TemplateResponse(
        "ranking/list.html",
        {"request": request, "decisions": decisions, "current_queue": queue}
    )

@router.get("/{decision_id}", response_class=HTMLResponse)
def view_decision(request: Request, decision_id: str, db: Session = Depends(get_db)):
    decision = db.query(ListingDecisionModel).filter_by(ranking_decision_id=decision_id).first()
    return templates.TemplateResponse(
        "ranking/detail.html",
        {"request": request, "decision": decision}
    )
