"""Immutable seed; content is loaded only from this app-owned package."""
import json
from pathlib import Path
from types import MappingProxyType

from pydantic import ConfigDict

from app.api.schemas import FileMetadata


class CanonicalDocument(FileMetadata):
    model_config = ConfigDict(extra='forbid', frozen=True)
    content: str


MANIFEST = MappingProxyType({
    item['id']: CanonicalDocument.model_validate(item)
    for item in json.loads(Path(__file__).with_name('documents.json').read_text(encoding='utf-8'))
})
# D01 must be generated from recorded events in Phase 4, never seeded.
