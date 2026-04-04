from fastapi import HTTPException

from app.services import reports as reports_service


class _Result:
    def __init__(self, data):
        self.data = data


class _NoopQuery:
    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def gte(self, *_args, **_kwargs):
        return self

    def lte(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        return _Result({})

class _ReportsQuery(_NoopQuery):
    def __init__(self, rows):
        self.rows = rows

    def execute(self):
        return _Result(self.rows)


class _CaptureQuery(_NoopQuery):
    def __init__(self, rows):
        self.rows = rows
        self.filters = []

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def execute(self):
        return _Result(self.rows)


def test_upvote_conflict_returns_409(monkeypatch):
    class _UpvotesConflictQuery(_NoopQuery):
        def insert(self, _payload):
            return self

        def execute(self):
            raise Exception("duplicate key value violates unique constraint 23505")

    class _Client:
        def table(self, name):
            if name == "upvotes":
                return _UpvotesConflictQuery()
            if name == "reports":
                return _NoopQuery()
            return _NoopQuery()

    monkeypatch.setattr(reports_service, "get_supabase_client", lambda: _Client())

    try:
        reports_service.upvote_report("r1", "u1")
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "already upvoted" in str(exc.detail).lower()


def test_upvote_escalates_at_threshold(monkeypatch):
    state = {"updated": None}

    class _UpvotesInsertQuery(_NoopQuery):
        def insert(self, _payload):
            return self

        def execute(self):
            return _Result([{"id": "up1"}])

    class _ReportsSelectQuery(_NoopQuery):
        def single(self):
            return self

        def execute(self):
            return _Result({"upvotes": 4, "status": "open"})

    class _ReportsUpdateQuery(_NoopQuery):
        def update(self, payload):
            state["updated"] = payload
            return self

        def execute(self):
            return _Result([{"id": "r1"}])

    class _Client:
        def table(self, name):
            if name == "upvotes":
                return _UpvotesInsertQuery()
            if name == "reports":
                class _TableSelector(_NoopQuery):
                    def select(self, *_args, **_kwargs):
                        return _ReportsSelectQuery()

                    def update(self, payload):
                        return _ReportsUpdateQuery().update(payload)

                return _TableSelector()
            return _NoopQuery()

    monkeypatch.setattr(reports_service, "get_supabase_client", lambda: _Client())
    result = reports_service.upvote_report("r1", "u1")

    assert result["upvotes"] == 5
    assert result["status"] == "escalated"
    assert state["updated"]["upvotes"] == 5
    assert state["updated"]["status"] == "escalated"


def test_admin_area_filter_is_case_insensitive(monkeypatch):
    rows = [
        {"id": "r1", "area_name": "Downtown Central", "severity": "high"},
        {"id": "r2", "location": "Riverside", "severity": "low"},
    ]

    class _Client:
        def table(self, name):
            if name == "reports":
                return _ReportsQuery(rows)
            return _NoopQuery()

    monkeypatch.setattr(reports_service, "get_supabase_client", lambda: _Client())
    result = reports_service.list_admin_reports(area_name="downtown")

    assert len(result) == 1
    assert result[0]["id"] == "r1"


def test_list_reports_supports_user_id_filter(monkeypatch):
    query = _CaptureQuery([{"id": "r1", "user_id": "u1"}])

    class _Client:
        def table(self, name):
            if name == "reports":
                return query
            return _NoopQuery()

    monkeypatch.setattr(reports_service, "get_supabase_client", lambda: _Client())
    result = reports_service.list_reports(user_id="u1")

    assert result == [{"id": "r1", "user_id": "u1"}]
    assert ("user_id", "u1") in query.filters
