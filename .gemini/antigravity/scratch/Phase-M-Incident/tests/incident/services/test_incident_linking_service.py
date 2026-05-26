import pytest
import uuid
from src.incident.services.incident_linking_service import IncidentLinkingService
from src.incident.models.incident_link import IncidentLinkEntityType, IncidentLink

class MockLinkRepo:
    def __init__(self):
        self.links = []
    def get_links_for_incident(self, incident_id, entity_type):
        return [l for l in self.links if l.incident_id == incident_id and l.entity_type == entity_type]
    def save_link(self, link):
        self.links.append(link)
    def delete_link(self, link_id):
        for i, l in enumerate(self.links):
            if l.link_id == link_id:
                del self.links[i]
                return True
        return False

# 19. link_attempts
def test_link_attempts():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    links = svc.link_attempts(inc_id, ["a1", "a2"])
    assert len(links) == 2
    assert links[0].entity_type == IncidentLinkEntityType.ATTEMPT
    assert repo.links[0].entity_id == "a1"

# 20. link_attempts deduplicates existing
def test_link_attempts_dedupes():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    svc.link_attempts(inc_id, ["a1"])
    links2 = svc.link_attempts(inc_id, ["a1", "a2"])
    assert len(links2) == 1
    assert links2[0].entity_id == "a2"
    assert len(repo.links) == 2

# 21. link_listings
def test_link_listings():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    links = svc.link_listings(inc_id, ["l1"])
    assert len(links) == 1
    assert links[0].entity_type == IncidentLinkEntityType.LISTING

# 22. link_alerts
def test_link_alerts():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    links = svc.link_alerts(inc_id, ["al1"])
    assert len(links) == 1
    assert links[0].entity_type == IncidentLinkEntityType.ALERT

# 23. link_reports
def test_link_reports():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    links = svc.link_reports(inc_id, ["r1"])
    assert len(links) == 1
    assert links[0].entity_type == IncidentLinkEntityType.REPORT

# 24. link_seller
def test_link_seller():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    link = svc.link_seller(inc_id, "s1")
    assert link is not None
    assert link.entity_type == IncidentLinkEntityType.SELLER
    assert link.entity_id == "s1"

# 25. link_environment
def test_link_environment():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    link = svc.link_environment(inc_id, "env1")
    assert link is not None
    assert link.entity_type == IncidentLinkEntityType.ENVIRONMENT

# 26. get_linked_entities
def test_get_linked_entities():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    svc.link_attempts(inc_id, ["a1", "a2"])
    entities = svc.get_linked_entities(inc_id, IncidentLinkEntityType.ATTEMPT)
    assert set(entities) == {"a1", "a2"}

# 27. unlink_entity
def test_unlink_entity():
    repo = MockLinkRepo()
    svc = IncidentLinkingService(repo)
    inc_id = uuid.uuid4()
    links = svc.link_attempts(inc_id, ["a1"])
    link_id = links[0].link_id
    res = svc.unlink_entity(link_id)
    assert res is True
    assert len(repo.links) == 0
