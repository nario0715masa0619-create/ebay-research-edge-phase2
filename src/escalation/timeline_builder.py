from typing import List, Dict, Any
from datetime import datetime
from src.escalation.models import EscalationTimelineItem, EscalationNote
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository
from src.repositories.persistent_escalation_note_repository import PersistentEscalationNoteRepository

class TimelineBuilder:
    def __init__(self, state_repo: PersistentEscalationStateRepository, note_repo: PersistentEscalationNoteRepository):
        self.state_repo = state_repo
        self.note_repo = note_repo

    def build_timeline(self, state_id: str) -> List[EscalationTimelineItem]:
        timeline: List[EscalationTimelineItem] = []
        
        # 1. Fetch Transitions
        transitions = self.state_repo.list_timeline_source_items(state_id)
        for t in transitions:
            timeline.append(EscalationTimelineItem(
                item_type=t["action_type"],
                timestamp=t["created_at"],
                actor=t["actor_id"] or t["actor_type"],
                description=t.get("note") or f"State changed to {t['new_status']}",
                meta=t.get("meta_json") or {}
            ))

        # 2. Fetch Notes
        notes = self.note_repo.list_notes_for_state(state_id)
        for n in notes:
            timeline.append(EscalationTimelineItem(
                item_type="note",
                timestamp=n.created_at,
                actor=n.author_id,
                description=n.body,
                meta={"is_internal": n.is_internal, "note_id": n.note_id}
            ))

        # 3. Sort Chronologically
        timeline.sort(key=lambda x: x.timestamp)
        return timeline
