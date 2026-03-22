from typing import Dict, Optional
from ..dto.backend_dto import BackendConnection, BackendConfig, BackendStatus

class BackendService:
    """Service layer for backend operations."""

    def __init__(self):
        self._backends: Dict[str, BackendConnection] = {}

    async def list_backends(self) -> list[BackendConnection]:
        return list(self._backends.values())

    async def get_backend(self, provider: str) -> Optional[BackendConnection]:
        return self._backends.get(provider)

    async def connect(self, config: BackendConfig) -> BackendConnection:
        backend = BackendConnection(
            provider=config.provider,
            status=BackendStatus.CONNECTED,
            host=config.host,
            port=config.port,
            database=config.database
        )
        self._backends[config.provider.value] = backend
        return backend

    async def disconnect(self, provider: str) -> bool:
        if provider in self._backends:
            self._backends[provider].status = BackendStatus.DISCONNECTED
            return True
        return False