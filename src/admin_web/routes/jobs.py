from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.action_guards import WebActionGuard
from src.admin_web.app import templates
import uuid
import datetime

router = APIRouter()

@router.get("/jobs", response_class=HTMLResponse)
async def list_jobs(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    # 1. Fetch registered jobs from the orchestrator registry
    jobs = container.job_service.list_jobs()
    
    job_views = []
    for j in jobs:
        # Check last run status in jobruns repository
        runs = container.jobrun_service.job_run_repo.list_recent(limit=100)
        job_runs = [r for r in runs if r.job_name == j["job_name"] and r.seller_account_id == active_context.seller_account_id]
        
        last_run_status = "never_run"
        last_run_started = None
        last_run_finished = None
        failure_reason = None
        
        if job_runs:
            # Sort by started_at descending to find the latest
            job_runs.sort(key=lambda x: x.started_at, reverse=True)
            last_run = job_runs[0]
            last_run_status = last_run.status
            last_run_started = last_run.started_at
            last_run_finished = last_run.finished_at
            failure_reason = last_run.error_summary
            
        job_views.append({
            "job_name": j["job_name"],
            "enabled": True, # Orchestrator jobs are enabled
            "schedule_type": j["schedule"] or "Manual / Ad-hoc",
            "last_run_status": last_run_status,
            "last_run_started_at": last_run_started,
            "last_run_finished_at": last_run_finished,
            "failure_reason": failure_reason
        })
        
    # Get overall jobruns history (paginated)
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 10))
    
    all_runs = container.jobrun_service.job_run_repo.list_recent(limit=100)
    # Filter by active context
    filtered_runs = [r for r in all_runs if r.seller_account_id == active_context.seller_account_id]
    filtered_runs.sort(key=lambda x: x.started_at, reverse=True)
    
    total_items = len(filtered_runs)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_runs = filtered_runs[start:end]
    
    from src.admin_web.pagination import PaginationHelper
    params = dict(request.query_params)
    paginator = PaginationHelper(total_items, page, page_size, "/admin/jobs", params)
    
    context = BaseLayoutContextBuilder.build(request, "Jobs & Runs")
    context.update({
        "jobs": job_views,
        "jobruns": paginated_runs,
        "paginator": paginator
    })
    return templates.TemplateResponse(request=request, name="jobs/list.html", context=context)

@router.get("/jobruns/{run_id}", response_class=HTMLResponse)
async def show_jobrun(request: Request, run_id: str):
    container = WebBootstrap.get_container()
    
    run = container.jobrun_service.job_run_repo.get_by_run_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"JobRun {run_id} not found.")
        
    context = BaseLayoutContextBuilder.build(request, f"Job Run: {run_id[:8]}")
    context.update({
        "run": run
    })
    return templates.TemplateResponse(request=request, name="jobs/show.html", context=context)

@router.post("/jobs/run")
async def trigger_job_run(
    request: Request,
    job_name: str = Form(...),
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    # 1. Guard check read-only / safety
    WebActionGuard.check_mutation_allowed(request)
    WebActionGuard.validate_environment_safety(request, environment_type)
    
    container = WebBootstrap.get_container()
    
    # 2. Trigger job execution inside orchestrator context
    try:
        res = container.job_service.run_job(job_name, dry_run=False)
        if res.exit_code == 0:
            request.state.flash(f"Manual job execution '{job_name}' completed successfully (Run ID: {res.summary['run_id'][:8]}...)", "success")
        else:
            request.state.flash(f"Manual job execution failed: {res.errors}", "error")
    except Exception as e:
        request.state.flash(f"Execution failed: {str(e)}", "error")
        
    return RedirectResponse(url=f"/admin/jobs?seller_account_id={seller_account_id}&environment_type={environment_type}", status_code=303)

@router.post("/scheduler/run-once")
async def trigger_scheduler_once(
    request: Request,
    seller_account_id: str = Form(...),
    environment_type: str = Form(...)
):
    WebActionGuard.check_mutation_allowed(request)
    
    # Trigger all active scheduler tasks once
    container = WebBootstrap.get_container()
    try:
        res = container.scheduler_service.run_once(dry_run=False)
        if res.exit_code == 0:
            request.state.flash("Scheduler executed all due tasks successfully.", "success")
        else:
            request.state.flash(f"Scheduler execution failed: {res.errors}", "error")
    except Exception as e:
        request.state.flash(f"Scheduler execution failed: {str(e)}", "error")
        
    return RedirectResponse(url=f"/admin/dashboard?seller_account_id={seller_account_id}&environment_type={environment_type}", status_code=303)
