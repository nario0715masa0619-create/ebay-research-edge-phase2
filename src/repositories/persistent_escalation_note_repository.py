import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from src.db.models import EscalationNoteModel
from src.escalation.models import EscalationNote

class PersistentEscalationNoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_note(self, state_id: str, author_id: str, author_type: str, body: str, is_internal: bool = True) -> EscalationNote:
        model = EscalationNoteModel(
            note_id=str(uuid.uuid4()),
            state_id=state_id,
            author_id=author_id,
            author_type=author_type,
            body=body,
            is_internal=is_internal,
            created_at=datetime.now()
        )
        self.session.add(model)
        self.session.commit()
        return self._to_domain(model)

    def list_notes_for_state(self, state_id: str) -> List[EscalationNote]:
        stmt = select(EscalationNoteModel).where(EscalationNoteModel.state_id == state_id).order_by(EscalationNoteModel.created_at.desc())
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def delete_note(self, note_id: str) -> bool:
        stmt = delete(EscalationNoteModel).where(EscalationNoteModel.note_id == note_id)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def _to_domain(self, model: EscalationNoteModel) -> EscalationNote:
        return EscalationNote(
            note_id=model.note_id,
            state_id=model.state_id,
            author_id=model.author_id,
            author_type=model.author_type,
            body=model.body,
            is_internal=model.is_internal,
            created_at=model.created_at
        )
