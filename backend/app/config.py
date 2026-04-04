"""
EcoSnap — Configuration & Supabase REST Client
Replaces the supabase SDK with direct PostgREST calls via httpx.
Works perfectly on Python 3.14 — zero dependency conflicts.
"""
import os
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Raw env values ─────────────────────────────────────────────────────────────
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_ANON_KEY: str = os.environ.get("ANON_PUBLIC", "") or os.environ.get("anonpublic", "")

GOOGLE_VISION_API_KEY: str = os.environ.get("CLOUD_VISION_API_KEY", "") or os.environ.get("Cloud_Vision", "")
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("Gemini", "")
GEMINI_MODEL: str = os.environ.get("MODEL_NAME", "") or os.environ.get("Model_Name", "gemini-2.0-flash")

# ── Supabase REST base URL ─────────────────────────────────────────────────────
SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""

# Common headers for all Supabase REST calls
SUPABASE_HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


class SupabaseClient:
    """
    Lightweight Supabase PostgREST wrapper using httpx.
    Replaces the broken supabase-py SDK on Python 3.14.
    Supports: select, insert, update, delete, eq, in_, order, limit, single, rpc.
    """

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "SUPABASE_URL or SUPABASE_SERVICE_KEY is not set. Check your .env file."
            )
        self._client = httpx.Client(timeout=15.0)

    def table(self, name: str) -> "QueryBuilder":
        return QueryBuilder(self._client, name)

    def rpc(self, fn_name: str, params: dict | None = None) -> "RpcBuilder":
        return RpcBuilder(self._client, fn_name, params or {})


class RpcBuilder:
    """Calls a Supabase RPC (stored procedure)."""

    def __init__(self, client: httpx.Client, fn_name: str, params: dict):
        self._client = client
        self._fn_name = fn_name
        self._params = params

    def execute(self) -> Any:
        url = f"{SUPABASE_REST_URL}/rpc/{self._fn_name}"
        resp = self._client.post(url, headers=SUPABASE_HEADERS, json=self._params)
        if resp.status_code >= 400:
            logger.warning(f"RPC {self._fn_name} failed: {resp.status_code} {resp.text}")
        return _SupabaseResult(resp)


class QueryBuilder:
    """
    Chainable query builder that mirrors the supabase-py API.
    Usage: supabase.table("reports").select("*").eq("id", x).execute()
    """

    def __init__(self, client: httpx.Client, table: str):
        self._client = client
        self._table = table
        self._url = f"{SUPABASE_REST_URL}/{table}"
        self._method = "GET"
        self._params: dict[str, str] = {}
        self._headers: dict[str, str] = dict(SUPABASE_HEADERS)
        self._body: Any = None
        self._is_single = False
        self._count_mode: str | None = None

    # ── Select ──────────────────────────────────────────────────────────────
    def select(self, columns: str = "*", count: str | None = None) -> "QueryBuilder":
        self._method = "GET"
        self._params["select"] = columns
        if count:
            self._count_mode = count
            self._headers["Prefer"] = f"count={count}"
        return self

    # ── Insert ──────────────────────────────────────────────────────────────
    def insert(self, data: dict | list) -> "QueryBuilder":
        self._method = "POST"
        self._body = data
        return self

    # ── Update ──────────────────────────────────────────────────────────────
    def update(self, data: dict) -> "QueryBuilder":
        self._method = "PATCH"
        self._body = data
        return self

    # ── Delete ──────────────────────────────────────────────────────────────
    def delete(self) -> "QueryBuilder":
        self._method = "DELETE"
        return self

    # ── Filters ─────────────────────────────────────────────────────────────
    def eq(self, column: str, value: Any) -> "QueryBuilder":
        self._params[column] = f"eq.{value}"
        return self

    def neq(self, column: str, value: Any) -> "QueryBuilder":
        self._params[column] = f"neq.{value}"
        return self

    def gt(self, column: str, value: Any) -> "QueryBuilder":
        self._params[column] = f"gt.{value}"
        return self

    def gte(self, column: str, value: Any) -> "QueryBuilder":
        self._params[column] = f"gte.{value}"
        return self

    def lt(self, column: str, value: Any) -> "QueryBuilder":
        self._params[column] = f"lt.{value}"
        return self

    def lte(self, column: str, value: Any) -> "QueryBuilder":
        self._params[column] = f"lte.{value}"
        return self

    def in_(self, column: str, values: list) -> "QueryBuilder":
        vals_str = ",".join(str(v) for v in values)
        self._params[column] = f"in.({vals_str})"
        return self

    # ── Modifiers ───────────────────────────────────────────────────────────
    def order(self, column: str, desc: bool = False) -> "QueryBuilder":
        direction = "desc" if desc else "asc"
        self._params["order"] = f"{column}.{direction}"
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._headers["Range"] = f"0-{n - 1}"
        return self

    def single(self) -> "QueryBuilder":
        self._is_single = True
        self._headers["Accept"] = "application/vnd.pgrst.object+json"
        return self

    # ── Execute ─────────────────────────────────────────────────────────────
    def execute(self) -> "_SupabaseResult":
        if self._method == "GET":
            resp = self._client.get(self._url, params=self._params, headers=self._headers)
        elif self._method == "POST":
            resp = self._client.post(
                self._url, params=self._params, headers=self._headers, json=self._body
            )
        elif self._method == "PATCH":
            resp = self._client.patch(
                self._url, params=self._params, headers=self._headers, json=self._body
            )
        elif self._method == "DELETE":
            resp = self._client.delete(
                self._url, params=self._params, headers=self._headers
            )
        else:
            raise ValueError(f"Unknown method: {self._method}")

        if resp.status_code >= 400:
            logger.error(f"Supabase {self._method} {self._table}: {resp.status_code} {resp.text}")

        return _SupabaseResult(resp, is_single=self._is_single, count_mode=self._count_mode)


class _SupabaseResult:
    """Wraps httpx.Response to match supabase-py result interface: .data, .count"""

    def __init__(self, response: httpx.Response, is_single: bool = False, count_mode: str | None = None):
        self._response = response
        self.count: int | None = None

        # Parse response body
        try:
            body = response.json()
        except Exception:
            body = None

        if is_single:
            self.data = body if isinstance(body, dict) else None
        elif isinstance(body, list):
            self.data = body
        elif isinstance(body, dict):
            self.data = [body]
        else:
            self.data = []

        # Parse count from Content-Range header if count mode was requested
        if count_mode:
            content_range = response.headers.get("Content-Range", "")
            # Format: "0-9/42" or "*/42"
            if "/" in content_range:
                try:
                    self.count = int(content_range.split("/")[1])
                except (ValueError, IndexError):
                    self.count = len(self.data) if isinstance(self.data, list) else 0
            else:
                self.count = len(self.data) if isinstance(self.data, list) else 0


# ── Singleton client ──────────────────────────────────────────────────────────
supabase = SupabaseClient()
