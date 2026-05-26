from typing import Optional, List, Dict, Any
import datetime
import uuid
from src.incident.models.incident import Incident, IncidentStatus, IncidentType
from src.incident.models.incident_event import IncidentEvent, IncidentEventType

class IncidentDeduplicationService:
    def __init__(self, incident_repo=None, event_repo=None):
        self.incident_repo = incident_repo
        self.event_repo = event_repo

    def is_dedupe_candidate(self, incident: Incident) -> bool:
        return incident.incident_status in [
            IncidentStatus.OPEN,
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.INVESTIGATING
        ]

    def check_duplicate_exists(self, 
                               incident_type: IncidentType, 
                               seller: Optional[str], 
                               environment: Optional[str], 
                               error_code: Optional[str], 
                               time_window_minutes: int = 30) -> Optional[uuid.UUID]:
        if not self.incident_repo:
            return None
        
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=time_window_minutes)
        recent_incidents = self.incident_repo.get_recent_incidents(since=cutoff_time)
        
        for inc in recent_incidents:
            if not self.is_dedupe_candidate(inc):
                continue
            
            # Match rules
            if inc.incident_type != incident_type:
                continue
            if inc.seller_account_id != seller:
                continue
            if inc.environment != environment:
                continue
            if inc.root_cause_code != error_code:
                # Assuming root_cause_code maps to error_code at detection time for matching
                continue
                
            return inc.incident_id
            
        return None

    def mark_as_duplicate(self, new_incident: Incident, existing_incident_id: uuid.UUID, actor: str = "system") -> bool:
        new_incident.incident_status = IncidentStatus.CANCELLED
        new_incident.duplicate_of_incident_id = existing_incident_id
        new_incident.closed_at = datetime.datetime.utcnow()
        # In a real system, we save this back to DB. Here we just update the object in memory.
        return True

    def add_event_to_existing(self, incident_id: uuid.UUID, event_type: IncidentEventType, details: Dict[str, Any]) -> bool:
        if not self.event_repo:
            return False
            
        event = IncidentEvent(
            event_id=uuid.uuid4(),
            incident_id=incident_id,
            event_type=event_type,
            note="Additional occurrence deduplicated",
            actor_type="system",
            actor_id="dedupe_service",
            details_json=details
        )
        self.event_repo.save_event(event)
        return True
