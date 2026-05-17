from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.action_guards import WebActionGuard
from src.admin_web.app import templates

router = APIRouter()

@router.get("/sellers", response_class=HTMLResponse)
async def list_sellers(request: Request):
    container = WebBootstrap.get_container()
    
    # List all seller accounts
    sellers = container.seller_ops.seller_repo.list_all()
    
    # Map additional view states
    seller_views = []
    for s in sellers:
        # Check active binding presence
        bindings = container.seller_ops.binding_repo.list_by_seller(s.seller_account_id)
        has_policy = bool(s.default_fulfillment_policy_id or s.default_payment_policy_id or s.default_return_policy_id)
        has_location = bool(s.default_merchant_location_key)
        
        seller_views.append({
            "seller_account_id": s.seller_account_id,
            "seller_name": s.seller_name,
            "seller_label": s.seller_label,
            "enabled": s.enabled,
            "environment_mode": s.environment_mode,
            "default_marketplace_id": s.default_marketplace_id,
            "has_policy_setup": has_policy,
            "has_location_setup": has_location,
            "active_bindings_count": len(bindings)
        })
        
    context = BaseLayoutContextBuilder.build(request, "Sellers List")
    context.update({
        "sellers": seller_views
    })
    return templates.TemplateResponse(request=request, name="sellers/list.html", context=context)

@router.get("/sellers/{seller_account_id}", response_class=HTMLResponse)
async def show_seller(request: Request, seller_account_id: str):
    container = WebBootstrap.get_container()
    
    seller = container.seller_ops.seller_repo.get_by_id(seller_account_id)
    if not seller:
        raise HTTPException(status_code=404, detail=f"Seller {seller_account_id} not found.")
        
    # Get associated active bindings
    bindings = container.seller_ops.binding_repo.list_by_seller(seller_account_id)
    
    # Get snapshot summaries
    policy_snapshots = container.seller_snapshot_ops.policy_repo.get_latest_for_seller(seller_account_id)
    location_snapshots = container.seller_snapshot_ops.location_repo.get_latest_for_seller(seller_account_id)
    
    context = BaseLayoutContextBuilder.build(request, f"Seller: {seller.seller_label}")
    context.update({
        "seller": seller,
        "bindings": bindings,
        "policy_snapshots": policy_snapshots,
        "location_snapshots": location_snapshots
    })
    return templates.TemplateResponse(request=request, name="sellers/show.html", context=context)

@router.post("/sellers/activate")
async def activate_seller_context(
    request: Request, 
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    # Safe mutation checks
    WebActionGuard.check_mutation_allowed(request)
    
    # Redirect with new query parameters
    redirect_url = f"/admin/dashboard?seller_account_id={seller_account_id}&environment_type={environment_type}"
    
    # Save flash message
    request.state.flash(f"Active context switched to: {seller_account_id} ({environment_type})", "success")
    
    return RedirectResponse(url=redirect_url, status_code=303)
