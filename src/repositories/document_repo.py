from domain.models import Document


class DocumentRepository:
    def __init__(self) -> None:
        self._documents: list[Document] = []

    def find_latest_by_checksum(self, checksum: str) -> Document | None:
        for doc in reversed(self._documents):
            if doc.checksum_sha256 == checksum and doc.is_latest:
                return doc
        return None

    def create(self, document: Document) -> Document:
        self._documents.append(document)
        return document

    def search(self, query: str | None = None, project: str | None = None, category: str | None = None) -> list[Document]:
        results = self._documents
        if query:
            q = query.lower()
            results = [doc for doc in results if q in doc.filename.lower()]
        if project:
            results = [doc for doc in results if doc.project.lower() == project.lower()]
        if category:
            results = [doc for doc in results if doc.category.lower() == category.lower()]
        return sorted(results, key=lambda d: d.uploaded_at, reverse=True)


document_repo = DocumentRepository()
