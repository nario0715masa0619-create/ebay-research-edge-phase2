from typing import List
from src.escalation.models import EscalationNote
from src.repositories.persistent_escalation_note_repository import PersistentEscalationNoteRepository

class NoteService:
    def __init__(self, repository: PersistentEscalationNoteRepository):
        self.repository = repository

    def add_note(self, state_id: str, body: str, author_id: str, author_type: str = "operator", is_internal: bool = True) -> EscalationNote:
        # We might add masking logic here later if needed, but for now we trust the operator
        # or implement masking at the display level.
        return self.repository.add_note(
            state_id=state_id,
            author_id=author_id,
            author_type=author_type,
            body=body,
            is_internal=is_internal
        )

    def list_notes(self, state_id: str) -> List[EscalationNote]:
        return self.repository.list_notes_for_state(state_id)
