from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.action_guards import WebActionGuard
from src.admin_web.app import templates
from src.admin_web.pagination import PaginationHelper
import json

router = APIRouter()

@router.get("/notifications", response_class=HTMLResponse)
async def list_notifications(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    severity = request.query_params.get("severity")
    q = request.query_params.get("q")
    
    notifications = container.notification_service.stats.repository.list_recent(limit=100)
    
    filtered = []
    for n in notifications:
        # Context match
        if n.seller_account_id != active_context.seller_account_id:
            continue
            
        # Severity filter
        if severity and n.severity != severity:
            continue
            
        # Search keyword match
        if q:
            if q.lower() not in n.event_type.lower() and (not n.sku or q.lower() not in n.sku.lower()):
                continue
                
        filtered.append(n)
        
    filtered.sort(key=lambda x: x.created_at or datetime.datetime.min, reverse=True)
    
    total_items = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]
    
    params = dict(request.query_params)
    paginator = PaginationHelper(total_items, page, page_size, "/admin/notifications", params)
    
    context = BaseLayoutContextBuilder.build(request, "Dispatched Notifications")
    context.update({
        "notifications": paginated,
        "paginator": paginator,
        "q": q or "",
        "severity": severity or ""
    })
    return templates.TemplateResponse(request=request, name="notifications/list.html", context=context)

@router.get("/notifications/{history_id}", response_class=HTMLResponse)
async def show_notification(request: Request, history_id: str):
    container = WebBootstrap.get_container()
    
    n = container.notification_service.stats.repository.get_by_history_id(int(history_id))
    if not n:
        raise HTTPException(status_code=404, detail=f"Notification History ID {history_id} not found.")
        
    # Masking sensitive details in payload summary to preserve security
    masked_payload = "None"
    if n.meta_json:
        try:
            masked_payload = json.dumps(container.notification_service.query.masker.mask_dict(n.meta_json), indent=2)
        except:
            masked_payload = "[UNPARSEABLE PAYLOAD] - MASKED FOR SAFETY"
            
    context = BaseLayoutContextBuilder.build(request, f"Notification: {history_id[:8]}")
    context.update({
        "notification": n,
        "masked_payload": masked_payload
    })
    return templates.TemplateResponse(request=request, name="notifications/show.html", context=context)

@router.post("/notifications/{history_id}/resend")
async def trigger_notification_resend(
    request: Request,
    history_id: str,
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    # Guard check read-only / safety
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.validate_environment_safety(request, environment_type)
    
    container = WebBootstrap.get_container()
    try:
        # Trigger manual resend
        container.notification_service.resend_notification(history_id=f"NTFH-{int(history_id):04d}")
        request.state.flash(f"Notification alert {history_id[:8]}... resent successfully.", "success")
    except Exception as e:
        request.state.flash(f"Resend failed: {str(e)}", "error")
        
    return RedirectResponse(url=f"/admin/notifications/{history_id}?seller_account_id={seller_account_id}&environment_type={environment_type}", status_code=303)

@router.post("/notifications/test")
async def trigger_test_notification(
    request: Request,
    event_type: str = Form(...),
    severity: str = Form(...),
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    # Guard check read-only / safety
    WebActionGuard.check_mutation_allowed(request)
    
    container = WebBootstrap.get_container()
    try:
        # Dispatch test event in notification framework
        container.notification_service.test_notification(
            channel="email",
            title=f"Web UI Test Event: {event_type}",
            summary=f"Dispatched test alert with severity={severity} for seller={seller_account_id}"
        )
        request.state.flash(f"Dispatched test notification ({event_type}) successfully.", "success")
    except Exception as e:
        request.state.flash(f"Test dispatch failed: {str(e)}", "error")
        
    return RedirectResponse(url=f"/admin/notifications?seller_account_id={seller_account_id}&environment_type={environment_type}", status_code=303)
