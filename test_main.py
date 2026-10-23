from datetime import date

from fastapi.testclient import TestClient

import main
from main import app, compute_streak

client = TestClient(app)


def test_create_and_list_habit():
    r = client.post("/habits", json={"name": "Read 20 minutes"})
    assert r.status_code == 200
    hid = r.json()["id"]
    r2 = client.get("/habits")
    assert r2.status_code == 200
    assert any(h["id"] == hid for h in r2.json())


def test_checkin_flow():
    hid = client.post("/habits", json={"name": "Stretch"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 200
    r2 = client.get(f"/habits/{hid}/checkins")
    assert r2.json() == ["2026-09-22"]


def test_checkin_unknown_habit_404():
    r = client.post("/habits/99999/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 404


TODAY = date(2026, 9, 22)


def _habit_with_checkins(days):
    hid = client.post("/habits", json={"name": "Streak habit"}).json()["id"]
    for day in days:
        assert client.post(f"/habits/{hid}/checkin", json={"day": day}).status_code == 200
    return hid


def test_compute_streak_empty():
    assert compute_streak([], TODAY) == 0


def test_compute_streak_counts_run_ending_today():
    days = ["2026-09-20", "2026-09-21", "2026-09-22"]
    assert compute_streak(days, TODAY) == 3


def test_compute_streak_still_current_before_todays_checkin():
    assert compute_streak(["2026-09-20", "2026-09-21"], TODAY) == 2


def test_compute_streak_zero_after_a_missed_day():
    assert compute_streak(["2026-09-19", "2026-09-20"], TODAY) == 0


def test_compute_streak_counts_today_once_it_is_checked():
    days = ["2026-09-20", "2026-09-21"]
    assert compute_streak(days + ["2026-09-22"], TODAY) == compute_streak(days, TODAY) + 1


def test_compute_streak_stops_at_gap():
    days = ["2026-09-17", "2026-09-18", "2026-09-20", "2026-09-21", "2026-09-22"]
    assert compute_streak(days, TODAY) == 3


def test_compute_streak_ignores_duplicates_future_and_bad_days():
    days = ["2026-09-22", "2026-09-22", "2026-09-21", "2026-09-23", "not-a-date", ""]
    assert compute_streak(days, TODAY) == 2


def test_compute_streak_crosses_month_boundary():
    days = ["2026-08-30", "2026-08-31", "2026-09-01"]
    assert compute_streak(days, date(2026, 9, 1)) == 3


def test_streak_endpoint(monkeypatch):
    monkeypatch.setattr(main, "today", lambda: TODAY)
    hid = _habit_with_checkins(["2026-09-19", "2026-09-21", "2026-09-22", "2026-09-20"])
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 4}


def test_streak_endpoint_no_checkins(monkeypatch):
    monkeypatch.setattr(main, "today", lambda: TODAY)
    hid = _habit_with_checkins([])
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 0}


def test_streak_endpoint_only_counts_own_habit(monkeypatch):
    monkeypatch.setattr(main, "today", lambda: TODAY)
    hid = _habit_with_checkins(["2026-09-22"])
    _habit_with_checkins(["2026-09-21"])
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 1


def test_streak_unknown_habit_404():
    r = client.get("/habits/99999/streak")
    assert r.status_code == 404
    assert r.json() == {"detail": "unknown habit"}
