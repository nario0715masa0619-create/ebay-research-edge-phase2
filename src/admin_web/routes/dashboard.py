from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.app import templates

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    # 1. Fetch Failed Jobs count
    # Check our PersistentJobRunRepository
    jobruns = container.jobrun_service.job_run_repo.list_recent(limit=100)
    failed_jobs = [r for r in jobruns if r.status == "failed" and r.seller_account_id == active_context.seller_account_id]
    
    # 2. Fetch Review Queue count
    reviews = container.review_service.candidate_repo.list_review_required()
    active_reviews = [c for c in reviews if c.seller_account_id == active_context.seller_account_id]
    
    # 3. Fetch notifications count and lists
    notifications = container.notification_service.stats.repository.list_recent(limit=100)
    active_notifications = [n for n in notifications if n.seller_account_id == active_context.seller_account_id]
    
    # 4. Fetch drifts count from listings
    listings = container.listing_service.listing_repo.list_all()
    active_listings = [l for l in listings if l.seller_account_id == active_context.seller_account_id]
    drifts_count = sum(1 for l in active_listings if l.offer_status == "drifted" or l.listing_status == "drifted")

    # Limit lists for layout
    recent_jobruns = jobruns[:5]
    recent_notifications = active_notifications[:5]
    
    # Build context layout
    context = BaseLayoutContextBuilder.build(request, "Dashboard Summary")
    context.update({
        "failed_jobs_count": len(failed_jobs),
        "review_queue_count": len(active_reviews),
        "recent_notifications_count": len(active_notifications),
        "recent_drifts_count": drifts_count,
        "recent_jobruns": recent_jobruns,
        "recent_notifications": recent_notifications
    })
    
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)
