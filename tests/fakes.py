"""Test doubles for unit 1. MOCK level — not integration (that is G4).

* ``FakeQdrantServer`` — in-memory Qdrant HTTP API behind ``httpx.MockTransport``. The
  carried ``QdrantClient`` runs unchanged down to the HTTP layer; only the server is fake.
* ``LexicalEmbeddings`` — deterministic hashing bag-of-words, 1536 dims, cosine-ready.
  It ranks by shared content words, so it proves wiring and thresholds, not semantics.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

import httpx

DIM = 1536
_STOP = set(
    "yang dan di ke dari untuk pada dengan atau ini itu adalah oleh setiap paling apa "
    "berapa kapan siapa bagaimana dalam sebagai tidak dapat ada the a of is what".split()
)


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 2]


class LexicalEmbeddings:
    model = "fake-lexical-1536"

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * DIM
        for tok in _tokens(text):
            v[int(hashlib.sha256(tok.encode()).hexdigest(), 16) % DIM] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    async def generate_query_embedding(self, query: str) -> list[float]:
        return self._vec(query)


class BrokenEmbeddings(LexicalEmbeddings):
    async def generate_query_embedding(self, query: str) -> list[float]:
        raise RuntimeError("401 invalid api key sk-should-never-appear-in-output")


class FakeQdrantServer:
    def __init__(self, fail_search: bool = False) -> None:
        self.collections: dict[str, dict[str, Any]] = {}
        self.fail_search = fail_search
        self.search_calls = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        parts = request.url.path.strip("/").split("/")
        if len(parts) < 2 or parts[0] != "collections":
            return httpx.Response(404, json={"status": {"error": "not found"}})
        name = parts[1]
        col = self.collections.get(name)
        if len(parts) == 2 and request.method == "PUT":
            self.collections[name] = {"points": {}}
            return httpx.Response(200, json={"result": True, "status": "ok"})
        if col is None:
            return httpx.Response(404, json={"status": {"error": f"Collection `{name}` doesn't exist!"}})
        if len(parts) == 2 and request.method == "GET":
            return httpx.Response(200, json={"result": {
                "status": "green", "points_count": len(col["points"]),
                "config": {"params": {"vectors": {"size": DIM, "distance": "Cosine"}}}}})
        body = httpx.Request("POST", "http://x", content=request.content).read()
        import json
        data = json.loads(body or b"{}")
        if parts[2:] == ["points"] and request.method == "PUT":
            for p in data["points"]:
                col["points"][str(p["id"])] = p
            return httpx.Response(200, json={"result": {"status": "completed"}, "status": "ok"})
        if parts[2:] == ["points", "search"] and request.method == "POST":
            self.search_calls += 1
            if self.fail_search:
                return httpx.Response(500, json={"status": {"error": "simulated server error"}})
            q = data["vector"]
            scored = []
            for p in col["points"].values():
                vec = p["vector"] if isinstance(p["vector"], list) else p["vector"].get("dense")
                scored.append({"id": p["id"], "score": sum(a * b for a, b in zip(q, vec)), "payload": p["payload"]})
            scored.sort(key=lambda r: r["score"], reverse=True)
            return httpx.Response(200, json={"result": scored[: data.get("limit", 5)], "status": "ok"})
        return httpx.Response(400, json={"status": {"error": f"unsupported {request.method} {request.url.path}"}})

    def attach(self, qdrant_client: Any) -> None:
        qdrant_client._http_client = httpx.AsyncClient(
            base_url=qdrant_client.qdrant_url, transport=httpx.MockTransport(self.handler)
        )
