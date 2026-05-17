from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.app import templates
from src.admin_web.pagination import PaginationHelper

router = APIRouter()

@router.get("/candidates", response_class=HTMLResponse)
async def list_candidates(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    # Extract query filters
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    q = request.query_params.get("q")
    status = request.query_params.get("status")
    
    # Query all candidates
    candidates = container.candidate_service.candidate_repo.list_all()
    
    # Filter candidates by context and inputs
    filtered = []
    for c in candidates:
        # Context match
        if c.seller_account_id != active_context.seller_account_id:
            continue
            
        # Status filter
        if status and c.status != status:
            continue
            
        # Search keyword match
        if q:
            q_lower = q.lower()
            title_match = c.source_title and q_lower in c.source_title.lower()
            sku_match = c.sku and q_lower in c.sku.lower()
            if not (title_match or sku_match):
                continue
                
        filtered.append(c)
        
    # Sort by standard score descending
    filtered.sort(key=lambda x: x.standard_score or 0.0, reverse=True)
    
    total_items = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]
    
    params = dict(request.query_params)
    paginator = PaginationHelper(total_items, page, page_size, "/admin/candidates", params)
    
    context = BaseLayoutContextBuilder.build(request, "Product Candidates")
    context.update({
        "candidates": paginated,
        "paginator": paginator,
        "q": q or "",
        "status": status or ""
    })
    return templates.TemplateResponse(request=request, name="candidates/list.html", context=context)

@router.get("/candidates/{sku}", response_class=HTMLResponse)
async def show_candidate(request: Request, sku: str):
    container = WebBootstrap.get_container()
    
    candidate = container.candidate_service.candidate_repo.get_by_sku(sku)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate Sku {sku} not found.")
        
    # Query candidate evidence log
    evidence_list = container.evidence_service.evidence_repo.get_by_candidate_id(candidate.candidate_id)
    
    # Related listings if any
    listing = container.listing_service.listing_repo.get_by_sku(sku)
    
    context = BaseLayoutContextBuilder.build(request, f"Candidate Sku: {sku}")
    context.update({
        "candidate": candidate,
        "evidence_list": evidence_list,
        "listing": listing
    })
    return templates.TemplateResponse(request=request, name="candidates/show.html", context=context)
