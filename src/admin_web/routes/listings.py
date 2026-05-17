from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.action_guards import WebActionGuard
from src.admin_web.app import templates
from src.admin_web.pagination import PaginationHelper
import datetime

router = APIRouter()

@router.get("/listings", response_class=HTMLResponse)
async def list_listings(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    q = request.query_params.get("q")
    status = request.query_params.get("status")
    
    listings = container.listing_service.listing_repo.list_all()
    
    filtered = []
    for l in listings:
        if l.seller_account_id != active_context.seller_account_id:
            continue
            
        if status and l.listing_status != status:
            continue
            
        if q:
            if q.lower() not in l.sku.lower():
                continue
                
        filtered.append(l)
        
    filtered.sort(key=lambda x: x.updated_at or datetime.datetime.min, reverse=True)
    
    total_items = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]
    
    params = dict(request.query_params)
    paginator = PaginationHelper(total_items, page, page_size, "/admin/listings", params)
    
    context = BaseLayoutContextBuilder.build(request, "Active Listings")
    context.update({
        "listings": paginated,
        "paginator": paginator,
        "q": q or "",
        "status": status or ""
    })
    return templates.TemplateResponse(request=request, name="listings/list.html", context=context)

@router.get("/listings/{sku}", response_class=HTMLResponse)
async def show_listing(request: Request, sku: str):
    container = WebBootstrap.get_container()
    
    listing = container.listing_service.listing_repo.get_by_sku(sku)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing Sku {sku} not found.")
        
    # Check remote drift or status
    candidate = container.candidate_service.candidate_repo.get_by_sku(sku)
    
    context = BaseLayoutContextBuilder.build(request, f"Listing: {sku}")
    context.update({
        "listing": listing,
        "candidate": candidate
    })
    return templates.TemplateResponse(request=request, name="listings/show.html", context=context)

@router.post("/listings/{sku}/sync")
async def trigger_listing_sync(
    request: Request,
    sku: str,
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    # Guard check read-only / safety
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.validate_environment_safety(request, environment_type)
    
    container = WebBootstrap.get_container()
    try:
        # Trigger re-synchronization using listing sync gateway
        container.listing_service.sync_listing(sku, dry_run=False)
        request.state.flash(f"Synchronization triggered successfully for SKU {sku}.", "success")
    except Exception as e:
        request.state.flash(f"Sync failed: {str(e)}", "error")
        
    return RedirectResponse(url=f"/admin/listings/{sku}?seller_account_id={seller_account_id}&environment_type={environment_type}", status_code=303)

@router.post("/listings/{sku}/recover")
async def trigger_listing_recover(
    request: Request,
    sku: str,
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.validate_environment_safety(request, environment_type)
    
    container = WebBootstrap.get_container()
    try:
        # Recover listing utilizing listing sync gateway
        container.listing_service.sync_listing(sku, dry_run=False, force_recheck=True)
        request.state.flash(f"Listing recovery action initiated for SKU {sku}.", "success")
    except Exception as e:
        request.state.flash(f"Recovery failed: {str(e)}", "error")
        
    return RedirectResponse(url=f"/admin/listings/{sku}?seller_account_id={seller_account_id}&environment_type={environment_type}", status_code=303)

@router.post("/listings/{sku}/withdraw")
async def trigger_listing_withdraw(
    request: Request,
    sku: str,
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.validate_environment_safety(request, environment_type)
    
    container = WebBootstrap.get_container()
    try:
        # Withdraw listing from remote market
        listing = container.listing_service.listing_repo.get_by_sku(sku)
        if listing:
            listing.listing_status = "withdrawn"
            listing.offer_status = "withdrawn"
            container.listing_service.listing_repo.upsert(listing)
            
        request.state.flash(f"Listing withdraw completed successfully for SKU {sku}.", "success")
    except Exception as e:
        request.state.flash(f"Withdraw failed: {str(e)}", "error")
        
    return RedirectResponse(url=f"/admin/listings/{sku}?seller_account_id={seller_account_id}&environment_type={environment_type}", status_code=303)
