"""Memory store abstraction for optional per-user conversation memory.

Design notes for Azure Cosmos DB usage:
- Use high-cardinality partition keys to avoid hot partitions.
- Prefer a hierarchical partition key shape based on tenant and user isolation.
  Example logical key value: "{tenantId}#{userId}".
- Keep items small and avoid unbounded message growth in a single item.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


class MemoryStore(Protocol):
    async def add_message(
        self,
        *,
        tenant_id: str,
        user_id: str,
        role: str,
        content: str,
        session_id: str | None = None,
    ) -> None: ...

    async def get_recent_messages(
        self,
        *,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        session_id: str | None = None,
    ) -> list[dict]: ...


@dataclass
class InMemoryStore:
    _items: dict[str, list[dict]]

    @classmethod
    def create(cls) -> "InMemoryStore":
        return cls(_items={})

    @staticmethod
    def _pk(tenant_id: str, user_id: str) -> str:
        return f"{tenant_id}#{user_id}"

    async def add_message(
        self,
        *,
        tenant_id: str,
        user_id: str,
        role: str,
        content: str,
        session_id: str | None = None,
    ) -> None:
        pk = self._pk(tenant_id, user_id)
        self._items.setdefault(pk, []).append(
            {
                "id": f"{datetime.now(UTC).timestamp()}:{len(self._items.get(pk, []))}",
                "pk": pk,
                "tenantId": tenant_id,
                "userId": user_id,
                "sessionId": session_id,
                "role": role,
                "content": content,
                "ts": datetime.now(UTC).isoformat(),
            }
        )

    async def get_recent_messages(
        self,
        *,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        session_id: str | None = None,
    ) -> list[dict]:
        pk = self._pk(tenant_id, user_id)
        messages = self._items.get(pk, [])
        if session_id:
            messages = [m for m in messages if m.get("sessionId") == session_id]
        return messages[-max(1, limit):]


class CosmosMemoryStore:
    """Optional Cosmos DB-backed store.

    Requires:
    - azure-cosmos package installed
    - COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE, COSMOS_CONTAINER env vars
    """

    def __init__(self, endpoint: str, key: str, database: str, container: str):
        from azure.cosmos.aio import CosmosClient  # local import to keep dependency optional

        self._endpoint = endpoint
        self._key = key
        self._database = database
        self._container_name = container
        self._client = CosmosClient(endpoint, credential=key)

    @staticmethod
    def _pk(tenant_id: str, user_id: str) -> str:
        return f"{tenant_id}#{user_id}"

    async def _container(self):
        db = self._client.get_database_client(self._database)
        return db.get_container_client(self._container_name)

    async def add_message(
        self,
        *,
        tenant_id: str,
        user_id: str,
        role: str,
        content: str,
        session_id: str | None = None,
    ) -> None:
        container = await self._container()
        pk = self._pk(tenant_id, user_id)
        item = {
            "id": f"{datetime.now(UTC).timestamp()}",
            "pk": pk,
            "tenantId": tenant_id,
            "userId": user_id,
            "sessionId": session_id,
            "role": role,
            "content": content,
            "ts": datetime.now(UTC).isoformat(),
        }
        await container.upsert_item(item)

    async def get_recent_messages(
        self,
        *,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        session_id: str | None = None,
    ) -> list[dict]:
        container = await self._container()
        pk = self._pk(tenant_id, user_id)

        query = "SELECT * FROM c WHERE c.pk = @pk"
        parameters = [{"name": "@pk", "value": pk}]
        if session_id:
            query += " AND c.sessionId = @sessionId"
            parameters.append({"name": "@sessionId", "value": session_id})
        query += " ORDER BY c.ts DESC"

        iterator = container.query_items(
            query=query,
            parameters=parameters,
            partition_key=pk,
            max_item_count=max(1, limit),
        )
        items = [item async for item in iterator]
        return list(reversed(items[: max(1, limit)]))


def build_memory_store() -> MemoryStore:
    backend = (os.getenv("MEMORY_BACKEND", "inmemory") or "inmemory").strip().lower()
    if backend != "cosmos":
        return InMemoryStore.create()

    endpoint = os.getenv("COSMOS_ENDPOINT")
    key = os.getenv("COSMOS_KEY")
    database = os.getenv("COSMOS_DATABASE")
    container = os.getenv("COSMOS_CONTAINER")

    if not all([endpoint, key, database, container]):
        return InMemoryStore.create()

    try:
        return CosmosMemoryStore(endpoint=endpoint, key=key, database=database, container=container)
    except Exception:
        # Keep local development resilient if Cosmos SDK/config is unavailable.
        return InMemoryStore.create()
