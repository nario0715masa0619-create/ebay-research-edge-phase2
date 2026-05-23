from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from src.admin_web.context import BaseLayoutContextBuilder
from src.admin_cli.services.discovery_review_ops_service import DiscoveryReviewOpsService
from src.discovery.review_queue_service import ReviewQueueService
from src.discovery.review_decision_service import ReviewDecisionService
from src.repositories.persistent_review_queue_repository import PersistentReviewQueueRepository, PersistentReviewAuditRepository
from src.repositories.persistent_alias_dictionary_repository import PersistentAliasDictionaryRepository

router = APIRouter(prefix="/discovery/review", tags=["discovery_review"])

def get_ops_service() -> DiscoveryReviewOpsService:
    q_repo = PersistentReviewQueueRepository()
    a_repo = PersistentReviewAuditRepository()
    al_repo = PersistentAliasDictionaryRepository()
    return DiscoveryReviewOpsService(
        ReviewQueueService(q_repo),
        ReviewDecisionService(q_repo, a_repo),
        al_repo
    )

def require_mutation_allowed(request: Request):
    ctx = BaseLayoutContextBuilder.build(request)
    if ctx.get("read_only_mode", False):
        raise HTTPException(status_code=403, detail="Mutation is not allowed in read-only mode")
    return ctx

@router.get("/", response_class=HTMLResponse)
async def list_reviews(request: Request, limit: int = 50, offset: int = 0):
    ctx = BaseLayoutContextBuilder.build(request, "Discovery Review Queue")
    ops = get_ops_service()
    
    items = ops.list_pending_reviews(limit=limit, offset=offset)
    
    # Just render using a new template
    return request.app.state.templates.TemplateResponse("discovery_review/list.html", {
        "request": request,
        "ctx": ctx,
        "items": items,
        "limit": limit,
        "offset": offset
    })

@router.get("/{candidate_id}", response_class=HTMLResponse)
async def show_review(request: Request, candidate_id: str):
    ctx = BaseLayoutContextBuilder.build(request, f"Review: {candidate_id}")
    ops = get_ops_service()
    
    view = ops.get_review_detail(candidate_id)
    if not view:
        if candidate_id == "alias": # Special case if alias gets intercepted here accidentally
            return RedirectResponse(url="/admin/discovery/review/alias/list")
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return request.app.state.templates.TemplateResponse("discovery_review/show.html", {
        "request": request,
        "ctx": ctx,
        "view": view
    })

@router.post("/{candidate_id}/decision")
async def make_decision(
    request: Request,
    candidate_id: str,
    action: str = Form(...),
    note: str = Form(None)
):
    ctx = require_mutation_allowed(request)
    ops = get_ops_service()
    actor = "admin_web"
    
    if action == "approve":
        ops.approve_candidate(candidate_id, actor, note)
        request.state.flash(f"Approved candidate {candidate_id}")
    elif action == "reject":
        ops.reject_candidate(candidate_id, actor, note)
        request.state.flash(f"Rejected candidate {candidate_id}")
    elif action == "hold":
        ops.hold_candidate(candidate_id, actor, note)
        request.state.flash(f"Hold candidate {candidate_id}", "warning")
    elif action == "reopen":
        ops.reopen_candidate(candidate_id, actor, note)
        request.state.flash(f"Reopened candidate {candidate_id}", "info")
    elif action == "note":
        ops.add_operator_note(candidate_id, actor, note or "No comment")
        request.state.flash("Note added.")
        
    return RedirectResponse(url=f"/admin/discovery/review/{candidate_id}", status_code=303)

@router.get("/alias/list", response_class=HTMLResponse)
async def list_aliases(request: Request):
    ctx = BaseLayoutContextBuilder.build(request, "Alias Dictionary")
    ops = get_ops_service()
    aliases = ops.list_aliases()
    
    return request.app.state.templates.TemplateResponse("discovery_review/alias_list.html", {
        "request": request,
        "ctx": ctx,
        "aliases": aliases
    })

@router.post("/alias/add")
async def add_alias(
    request: Request,
    alias_type: str = Form(...),
    token: str = Form(...),
    resolution: str = Form(...)
):
    ctx = require_mutation_allowed(request)
    ops = get_ops_service()
    
    ops.add_alias("admin_web", alias_type, token, resolution)
    request.state.flash(f"Added alias for '{token}'")
    return RedirectResponse(url="/admin/discovery/review/alias/list", status_code=303)

@router.post("/alias/{alias_id}/disable")
async def disable_alias(request: Request, alias_id: str):
    ctx = require_mutation_allowed(request)
    ops = get_ops_service()
    
    ops.disable_alias("admin_web", alias_id)
    request.state.flash(f"Disabled alias {alias_id}", "warning")
    return RedirectResponse(url="/admin/discovery/review/alias/list", status_code=303)
