from typing import List, Optional, Set
import uuid
from src.incident.models.incident_link import IncidentLink, IncidentLinkEntityType

class IncidentLinkingService:
    def __init__(self, link_repo=None):
        # Using a mock repo for tests
        self.link_repo = link_repo
        
    def _create_links(self, incident_id: uuid.UUID, entity_type: IncidentLinkEntityType, entity_ids: List[str]) -> List[IncidentLink]:
        existing_links = []
        if self.link_repo:
            existing_links = self.link_repo.get_links_for_incident(incident_id, entity_type)
            
        existing_entity_ids = {link.entity_id for link in existing_links}
        new_links = []
        
        for e_id in entity_ids:
            if e_id not in existing_entity_ids:
                link = IncidentLink(
                    link_id=uuid.uuid4(),
                    incident_id=incident_id,
                    entity_type=entity_type,
                    entity_id=e_id
                )
                if self.link_repo:
                    self.link_repo.save_link(link)
                new_links.append(link)
                existing_entity_ids.add(e_id) # prevent dupes in same batch
                
        return new_links

    def link_attempts(self, incident_id: uuid.UUID, attempt_ids: List[str]) -> List[IncidentLink]:
        return self._create_links(incident_id, IncidentLinkEntityType.ATTEMPT, attempt_ids)

    def link_listings(self, incident_id: uuid.UUID, listing_ids: List[str]) -> List[IncidentLink]:
        return self._create_links(incident_id, IncidentLinkEntityType.LISTING, listing_ids)

    def link_alerts(self, incident_id: uuid.UUID, alert_ids: List[str]) -> List[IncidentLink]:
        return self._create_links(incident_id, IncidentLinkEntityType.ALERT, alert_ids)

    def link_reports(self, incident_id: uuid.UUID, report_ids: List[str]) -> List[IncidentLink]:
        return self._create_links(incident_id, IncidentLinkEntityType.REPORT, report_ids)

    def link_seller(self, incident_id: uuid.UUID, seller_id: str) -> Optional[IncidentLink]:
        links = self._create_links(incident_id, IncidentLinkEntityType.SELLER, [seller_id])
        return links[0] if links else None

    def link_environment(self, incident_id: uuid.UUID, environment: str) -> Optional[IncidentLink]:
        links = self._create_links(incident_id, IncidentLinkEntityType.ENVIRONMENT, [environment])
        return links[0] if links else None

    def get_linked_entities(self, incident_id: uuid.UUID, entity_type: IncidentLinkEntityType) -> List[str]:
        if not self.link_repo:
            return []
        links = self.link_repo.get_links_for_incident(incident_id, entity_type)
        return [link.entity_id for link in links]

    def unlink_entity(self, link_id: uuid.UUID) -> bool:
        if not self.link_repo:
            return False
        return self.link_repo.delete_link(link_id)
