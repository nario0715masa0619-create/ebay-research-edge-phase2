import datetime
from typing import Optional

def incident_detection_job(detection_service, management_service):
    """
    Runs detection from alerts and creates incidents if needed.
    """
    # 1. Detect candidates
    candidates = detection_service.detect_from_alert_burst()
    
    # 2. Create incidents
    results = []
    for candidate in candidates:
        try:
            inc = management_service.create_incident_from_candidate(
                candidate=candidate,
                actor="orchestrator_job",
                trigger_source="incident_detection_job"
            )
            results.append(inc)
        except Exception as e:
            # log error and continue
            print(f"Error creating incident from candidate: {e}")
            
    return results

def incident_sla_evaluation_job(management_service, incident_repo, sla_service):
    """
    Evaluates open incidents for SLA breaches and records events if needed.
    """
    # 1. Get open incidents
    open_incs = incident_repo.get_open_incidents()
    
    breached_count = 0
    # 2. Evaluate SLA for each
    for inc in open_incs:
        # Evaluate SLA checks current time against due_ats
        breached = sla_service.evaluate_sla_state(inc)
        if breached:
            # If changed state to breached, we can record it
            # For simplicity, if we detect breach here, we can trigger management service
            # Actually ManagementService has a way to resolve/ack, but what if it just breaches while waiting?
            # We can directly update the repo and event.
            try:
                # We mock a management level SLA breach update
                management_service._state_machine.to_status(inc, inc.incident_status) # just for audit?
                # Actually, SLA breach might not change status, but changes sla_state.
                incident_repo.update_incident(inc.incident_id, {"sla_state": inc.sla_state})
                breached_count += 1
            except Exception as e:
                print(f"Error updating SLA state for {inc.incident_id}: {e}")
                
    return breached_count

def incident_overdue_digest_job(digest_service):
    """
    Generates a daily digest of overdue incidents.
    """
    now = datetime.datetime.utcnow()
    report = digest_service.generate_overdue_digest(now)
    # Output to stdout or save it
    print(f"Overdue Digest generated for {report.period}")
    return report
