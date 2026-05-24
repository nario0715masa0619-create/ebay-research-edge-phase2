from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.admin_web.dependencies import get_db, templates
from src.admin_cli.services.handoff_ops_service import HandoffOpsService
from src.db.models import ListingHandoffModel

router = APIRouter(prefix="/handoffs", tags=["handoffs"])

@router.get("/", response_class=HTMLResponse)
async def list_handoffs(request: Request, db: Session = Depends(get_db), limit: int = 50, status: str = None):
    query = db.query(ListingHandoffModel).order_by(ListingHandoffModel.created_at.desc())
    if status:
        query = query.filter(ListingHandoffModel.handoff_status == status)
        
    handoffs = query.limit(limit).all()
    
    return templates.TemplateResponse(
        "handoff/list.html",
        {"request": request, "handoffs": handoffs, "status_filter": status}
    )

@router.get("/{handoff_id}", response_class=HTMLResponse)
async def show_handoff(request: Request, handoff_id: str, db: Session = Depends(get_db)):
    ops = HandoffOpsService(db)
    handoff_res = ops.get_handoff_by_id(handoff_id)
    
    # Simple query for attempts/transitions (mocked passing via template for now)
    # Ideally we add get_transitions and get_attempts to the service.
    
    return templates.TemplateResponse(
        "handoff/detail.html",
        {"request": request, "handoff": handoff_res}
    )
