from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import BaseLayoutContextBuilder, SellerContextWebResolver
from src.admin_web.app import templates
import os

router = APIRouter()

@router.get("/doctor", response_class=HTMLResponse)
async def view_doctor_diagnostics(request: Request):
    container = WebBootstrap.get_container()
    active_context = SellerContextWebResolver.resolve(request)
    
    # 1. Database Diagnostic
    try:
        # Check active session
        session = WebBootstrap.get_db_session()
        session.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    # 2. Auth Diagnostic
    try:
        # Check auth token availability for active context
        token = container.doctor_service.token_service.get_access_token(
            seller_account_id=active_context.seller_account_id,
            environment_type=active_context.environment_type
        )
        auth_status = "ok" if token else "warning: token empty"
    except Exception as e:
        auth_status = f"error: {str(e)}"
        
    # 3. Scheduler Diagnostic
    try:
        # Inspect registered jobs count in engine
        jobs_count = len(container.job_service.orchestrator.registry.list_jobs())
        scheduler_status = f"ok ({jobs_count} jobs registered)"
    except Exception as e:
        scheduler_status = f"error: {str(e)}"
        
    # 4. Notification Channel Diagnostic
    try:
        channels_count = len(container.notification_service.stats_service.history_repo.list_all())
        notification_status = f"ok ({channels_count} historical alerts)"
    except Exception as e:
        notification_status = f"error: {str(e)}"
        
    # 5. Seller/Environment Consistency Check
    try:
        # Call doctor_service or seller_doctor
        binding = container.seller_doctor.resolver.binding_repo.get_active_for_seller(active_context.seller_account_id)
        if binding:
            seller_env_consistency = "consistent"
            policy_completeness = "complete" if binding.fulfillment_policy_id and binding.payment_policy_id and binding.return_policy_id else "incomplete policy default bindings"
        else:
            seller_env_consistency = "warning: no active binding configured"
            policy_completeness = "incomplete"
    except Exception as e:
        seller_env_consistency = f"error: {str(e)}"
        policy_completeness = "incomplete"

    # Assemble non-sensitive config summaries
    configs = {
        "ADMIN_WEB_ENABLED": os.environ.get("ADMIN_WEB_ENABLED", "true"),
        "ADMIN_WEB_HOST": os.environ.get("ADMIN_WEB_HOST", "127.0.0.1"),
        "ADMIN_WEB_PORT": os.environ.get("ADMIN_WEB_PORT", "8000"),
        "ADMIN_WEB_READ_ONLY_MODE": os.environ.get("ADMIN_WEB_READ_ONLY_MODE", "false"),
        "ADMIN_WEB_ENABLE_MUTATIONS": os.environ.get("ADMIN_WEB_ENABLE_MUTATIONS", "true"),
        "ADMIN_WEB_DEFAULT_PAGE_SIZE": os.environ.get("ADMIN_WEB_DEFAULT_PAGE_SIZE", "20"),
        "ADMIN_WEB_BASIC_AUTH_ENABLED": os.environ.get("ADMIN_WEB_BASIC_AUTH_ENABLED", "false"),
        "DEFAULT_SELLER_ACCOUNT_ID": os.environ.get("DEFAULT_SELLER_ACCOUNT_ID", "Not Set"),
        "DEFAULT_ENVIRONMENT_TYPE": os.environ.get("DEFAULT_ENVIRONMENT_TYPE", "Not Set"),
        "SELLER_ENV_ALLOW_SANDBOX_PUBLISH": os.environ.get("SELLER_ENV_ALLOW_SANDBOX_PUBLISH", "true"),
        "SELLER_ENV_ALLOW_PRODUCTION_PUBLISH": os.environ.get("SELLER_ENV_ALLOW_PRODUCTION_PUBLISH", "false")
    }

    context = BaseLayoutContextBuilder.build(request, "System Doctor Diagnostics")
    context.update({
        "db_status": db_status,
        "auth_status": auth_status,
        "scheduler_status": scheduler_status,
        "notification_status": notification_status,
        "seller_env_consistency": seller_env_consistency,
        "policy_completeness": policy_completeness,
        "configs": configs
    })
    
    return templates.TemplateResponse(request=request, name="doctor/index.html", context=context)
