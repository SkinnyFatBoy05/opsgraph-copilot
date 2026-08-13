"""Interface implemented by every OpsGraph business domain."""

from pathlib import Path
from typing import Protocol

from opsgraph.contracts.evidence import DomainName


class DomainAdapter(Protocol):
    @property
    def name(self) -> DomainName: ...

    @property
    def documents_path(self) -> Path: ...

    @property
    def schema(self) -> str: ...
