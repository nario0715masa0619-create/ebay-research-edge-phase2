from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime, timezone, timedelta
import os

from src.listing_execution.models.history_query import HistoryQuery
from src.listing_execution.services.execution_history_query_service import ExecutionHistoryQueryService
from src.listing_execution.services.execution_audit_timeline_service import ExecutionAuditTimelineService
from src.listing_execution.services.execution_dashboard_service import ExecutionDashboardService

router = APIRouter(prefix="/execution")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

def get_query_service():
    return ExecutionHistoryQueryService()

def get_timeline_service():
    return ExecutionAuditTimelineService()

def get_dashboard_service():
    return ExecutionDashboardService()

@router.get("/history")
def history_list(
    request: Request,
    attempt_id: Optional[str] = None,
    listing_id: Optional[str] = None,
    seller_account_id: Optional[str] = None,
    environment: Optional[str] = None,
    event_type: Optional[str] = None,
    dry_run: Optional[bool] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    query_service: ExecutionHistoryQueryService = Depends(get_query_service)
):
    f_date = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc) if from_date else None
    t_date = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) if to_date else None
    
    query = HistoryQuery(
        attempt_id=attempt_id,
        listing_id=listing_id,
        seller_account_id=seller_account_id,
        environment=environment,
        event_type=event_type,
        dry_run=dry_run,
        limit=limit,
        offset=(page - 1) * limit
    )
    if f_date and t_date:
        query.date_range = (f_date, t_date)
        
    result = query_service.apply_filters(query)
    
    total_pages = (result["total"] + limit - 1) // limit if limit > 0 else 1
    
    return templates.TemplateResponse(request=request, name="execution_history/list.html", context={
        "request": request,
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "total_pages": total_pages,
        "filters": {
            "attempt_id": attempt_id or "",
            "listing_id": listing_id or "",
            "seller_account_id": seller_account_id or "",
            "environment": environment or "",
            "event_type": event_type or "",
            "dry_run": str(dry_run) if dry_run is not None else "",
            "from_date": from_date or "",
            "to_date": to_date or ""
        }
    })

@router.get("/history/attempt/{attempt_id}")
def attempt_detail(
    request: Request,
    attempt_id: str,
    timeline_service: ExecutionAuditTimelineService = Depends(get_timeline_service)
):
    timeline = timeline_service.build_attempt_timeline(attempt_id)
    state_transitions = timeline_service.extract_state_transitions(timeline)
    critical_events = timeline_service.filter_critical_events(timeline)
    
    return templates.TemplateResponse(request=request, name="execution_history/attempt_detail.html", context={
        "request": request,
        "attempt_id": attempt_id,
        "timeline": timeline,
        "state_transitions": state_transitions,
        "critical_events": critical_events
    })

@router.get("/history/listing/{listing_id}")
def listing_detail(
    request: Request,
    listing_id: str,
    timeline_service: ExecutionAuditTimelineService = Depends(get_timeline_service)
):
    timeline = timeline_service.build_listing_timeline(listing_id)
    
    # Group by attempt_id
    attempts = {}
    for event in timeline:
        att = event.attempt_id
        if att not in attempts:
            attempts[att] = []
        attempts[att].append(event)
        
    # Sort attempts by the first event's created_at descending
    sorted_attempts = sorted(attempts.items(), key=lambda x: x[1][0].created_at, reverse=True)
    
    return templates.TemplateResponse(request=request, name="execution_history/listing_detail.html", context={
        "request": request,
        "listing_id": listing_id,
        "attempts": sorted_attempts
    })

@router.get("/dashboard")
def dashboard(
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    dashboard_service: ExecutionDashboardService = Depends(get_dashboard_service)
):
    f_date = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc) if from_date else datetime.now(timezone.utc) - timedelta(days=7)
    t_date = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) if to_date else datetime.now(timezone.utc)
    
    dr = (f_date, t_date)
    summary = dashboard_service.get_overview_summary(dr)
    recent_failures = dashboard_service.get_recent_failures(limit=10)
    
    return templates.TemplateResponse(request=request, name="execution_history/dashboard.html", context={
        "request": request,
        "summary": summary,
        "recent_failures": recent_failures,
        "filters": {
            "from_date": from_date or "",
            "to_date": to_date or ""
        }
    })
