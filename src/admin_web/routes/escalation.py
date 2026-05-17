from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.app import templates
from src.admin_web.action_guards import WebActionGuard

router = APIRouter(prefix="/escalations", tags=["escalations"])

@router.get("", response_class=HTMLResponse)
async def list_escalations(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    # Get active states for current seller
    active_states = container.escalation_service.list_active()
    filtered_active = [s for s in active_states if s.get("seller_account_id") == active_context.seller_account_id]
    
    # Get recent states
    recent_states = container.escalation_service.list_recent(limit=50)
    filtered_recent = [s for s in recent_states if s.get("seller_account_id") == active_context.seller_account_id]
    
    stats = container.escalation_service.stats()
    
    context = BaseLayoutContextBuilder.build(request, "Escalations & Reminders")
    context.update({
        "active_states": filtered_active,
        "recent_states": filtered_recent,
        "stats": stats
    })
    
    return templates.TemplateResponse(request=request, name="escalations/list.html", context=context)

@router.get("/{state_id}", response_class=HTMLResponse)
async def show_escalation(request: Request, state_id: str):
    container = WebBootstrap.get_container()
    
    state = container.escalation_service.get_details(state_id)
    if not state:
        raise HTTPException(status_code=404, detail="Escalation State not found")
        
    timeline_items = container.escalation_service.timeline(state_id)
    notes = container.escalation_service.list_notes(state_id)
        
    context = BaseLayoutContextBuilder.build(request, f"Escalation Details: {state_id}")
    context.update({"state": state, "timeline": timeline_items, "notes": notes})
    
    return templates.TemplateResponse(request=request, name="escalations/show.html", context=context)

@router.post("/{state_id}/ack")
async def ack_escalation(request: Request, state_id: str, note: str = Form(None), confirm: str = Form(None)):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.verify_confirmation(request, {"confirm": confirm})
    
    container = WebBootstrap.get_container()
    container.escalation_service.ack(state_id, actor_id="web_user", note=note)
    
    request.session["flash_message"] = f"Escalation {state_id} acknowledged successfully."
    return RedirectResponse(url=f"/escalations/{state_id}", status_code=303)

@router.post("/{state_id}/resolve")
async def resolve_escalation(request: Request, state_id: str, note: str = Form(None), confirm: str = Form(None)):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.verify_confirmation(request, {"confirm": confirm})
    
    container = WebBootstrap.get_container()
    container.escalation_service.resolve(state_id, actor_id="web_user", note=note)
    
    request.session["flash_message"] = f"Escalation {state_id} resolved successfully."
    return RedirectResponse(url=f"/escalations/{state_id}", status_code=303)

@router.post("/{state_id}/silence")
async def silence_escalation(request: Request, state_id: str, hours: int = Form(24), note: str = Form(None), confirm: str = Form(None)):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.verify_confirmation(request, {"confirm": confirm})
    
    container = WebBootstrap.get_container()
    container.escalation_service.silence(state_id, hours=hours, actor_id="web_user", note=note)
    
    request.session["flash_message"] = f"Escalation {state_id} silenced for {hours} hours."
    return RedirectResponse(url=f"/escalations/{state_id}", status_code=303)

@router.post("/{state_id}/notes")
async def add_note(request: Request, state_id: str, body: str = Form(...), confirm: str = Form(None)):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.verify_confirmation(request, {"confirm": confirm})
    container = WebBootstrap.get_container()
    container.escalation_service.add_note(state_id, body, actor_id="web_user")
    request.session["flash_message"] = "Note added successfully."
    return RedirectResponse(url=f"/escalations/{state_id}", status_code=303)

@router.post("/bulk/{action}")
async def bulk_action(request: Request, action: str, state_ids: str = Form(...), confirm: str = Form(None)):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.verify_confirmation(request, {"confirm": confirm})
    container = WebBootstrap.get_container()
    id_list = [i.strip() for i in state_ids.split(",") if i.strip()]
    if action == "ack":
        container.escalation_service.bulk_ack(id_list, "web_user")
    elif action == "resolve":
        container.escalation_service.bulk_resolve(id_list, "web_user")
    elif action == "silence":
        container.escalation_service.bulk_silence(id_list, 24, "web_user")
    request.session["flash_message"] = f"Bulk {action} completed for {len(id_list)} items."
    return RedirectResponse(url="/escalations", status_code=303)

@router.get("/maintenance/list", response_class=HTMLResponse)
async def list_maintenance(request: Request):
    container = WebBootstrap.get_container()
    windows = container.escalation_service.maintenance_list()
    context = BaseLayoutContextBuilder.build(request, "Maintenance Windows")
    context.update({"windows": windows})
    return templates.TemplateResponse(request=request, name="escalations/maintenance.html", context=context)

@router.post("/maintenance/add")
async def add_maintenance(request: Request, starts: str = Form(...), ends: str = Form(...), action: str = Form("suppress_all"), confirm: str = Form(None)):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.verify_confirmation(request, {"confirm": confirm})
    from datetime import datetime
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    container.escalation_service.maintenance_add(
        starts_at=datetime.fromisoformat(starts),
        ends_at=datetime.fromisoformat(ends),
        action=action,
        seller_account_id=active_context.seller_account_id,
        env=active_context.environment,
        event=None
    )
    request.session["flash_message"] = "Maintenance window created."
    return RedirectResponse(url="/escalations/maintenance/list", status_code=303)

@router.post("/maintenance/{window_id}/remove")
async def remove_maintenance(request: Request, window_id: str, confirm: str = Form(None)):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.verify_confirmation(request, {"confirm": confirm})
    container = WebBootstrap.get_container()
    container.escalation_service.maintenance_remove(window_id)
    request.session["flash_message"] = "Maintenance window removed."
    return RedirectResponse(url="/escalations/maintenance/list", status_code=303)

