from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.app import templates

router = APIRouter()

@router.get("/review", response_class=HTMLResponse)
async def list_review_queue(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    # Query candidates in failed/review status
    candidates = container.candidate_service.candidate_repo.list_review_required()
    
    # Filter candidates by active context
    reviews = []
    for c in candidates:
        if c.seller_account_id != active_context.seller_account_id:
            continue
            
        blockers = c.listing_blockers or []
        reason = ", ".join(blockers) if blockers else "Standard Validation Error"
        
        reviews.append({
            "candidate_id": c.candidate_id,
            "sku": c.sku,
            "title": c.source_title,
            "source_platform": c.source_platform or "Yahoo! Flea Market",
            "review_reason": reason,
            "severity": "critical" if "PROFIT_THRESHOLD_NOT_MET" not in blockers else "warning",
            "created_at": c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else "Unknown",
            "seller_account_id": c.seller_account_id,
            "environment_type": active_context.environment_type
        })
        
    context = BaseLayoutContextBuilder.build(request, "Review Queue")
    context.update({
        "reviews": reviews
    })
    return templates.TemplateResponse(request=request, name="review/list.html", context=context)
