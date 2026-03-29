from collections.abc import Sequence
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from db.models import DocumentRecord


class DocumentRepository:
    def find_latest_by_checksum(self, session: Session, checksum: str) -> DocumentRecord | None:
        stmt = select(DocumentRecord).where(
            DocumentRecord.checksum_sha256 == checksum,
            DocumentRecord.is_latest.is_(True),
        ).order_by(desc(DocumentRecord.created_at)).limit(1)
        return session.scalar(stmt)

    def find_by_id(self, session: Session, doc_id: str) -> DocumentRecord | None:
        return session.get(DocumentRecord, doc_id)

    def find_latest_in_logical_group(self, session: Session, logical_doc_id: str) -> DocumentRecord | None:
        stmt = select(DocumentRecord).where(DocumentRecord.logical_doc_id == logical_doc_id).order_by(desc(DocumentRecord.version)).limit(1)
        return session.scalar(stmt)

    def create(self, session: Session, **kwargs) -> DocumentRecord:
        record = DocumentRecord(**kwargs)
        session.add(record)
        session.flush()
        return record

    def mark_group_non_latest(self, session: Session, logical_doc_id: str) -> None:
        stmt = select(DocumentRecord).where(DocumentRecord.logical_doc_id == logical_doc_id, DocumentRecord.is_latest.is_(True))
        for rec in session.scalars(stmt):
            rec.is_latest = False

    def search(
        self,
        session: Session,
        *,
        query: str | None = None,
        project: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        uploader: str | None = None,
        limit: int = 20,
    ) -> Sequence[DocumentRecord]:
        stmt = select(DocumentRecord)
        clauses = []
        if query:
            like = f"%{query.lower()}%"
            clauses.append(or_(func.lower(DocumentRecord.filename).like(like), func.lower(DocumentRecord.original_filename).like(like)))
        if project:
            clauses.append(func.lower(DocumentRecord.project) == project.lower())
        if category:
            clauses.append(func.lower(DocumentRecord.category) == category.lower())
        if uploader:
            clauses.append(DocumentRecord.uploader_discord_id == uploader)
        if tags:
            for tag in tags:
                clauses.append(func.lower(DocumentRecord.tags_csv).like(f"%{tag.lower()}%"))
        if clauses:
            stmt = stmt.where(*clauses)
        stmt = stmt.order_by(desc(DocumentRecord.created_at)).limit(limit)
        return list(session.scalars(stmt))


document_repo = DocumentRepository()
