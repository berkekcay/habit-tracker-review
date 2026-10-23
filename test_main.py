import pytest
from fastapi.testclient import TestClient

from main import app

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


def error_messages(response):
    return [err["msg"] for err in response.json()["detail"]]


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_create_habit_rejects_blank_name(name):
    r = client.post("/habits", json={"name": name})
    assert r.status_code == 422
    assert error_messages(r) == ["habit name must not be empty"]


def test_create_habit_rejects_missing_name():
    r = client.post("/habits", json={})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["body", "name"]


def test_create_habit_rejects_too_long_name():
    r = client.post("/habits", json={"name": "x" * 101})
    assert r.status_code == 422
    assert error_messages(r) == ["habit name must be at most 100 characters"]


def test_create_habit_accepts_name_at_limit():
    r = client.post("/habits", json={"name": "x" * 100})
    assert r.status_code == 200


def test_create_habit_strips_surrounding_whitespace():
    r = client.post("/habits", json={"name": "  Meditate  "})
    assert r.status_code == 200
    assert r.json()["name"] == "Meditate"


@pytest.mark.parametrize(
    "day",
    ["", "yesterday", "2026/09/22", "20260922", "22-09-2026", "2026-9-22", "2026-09-22T08:00"],
)
def test_checkin_rejects_malformed_day(day):
    hid = client.post("/habits", json={"name": "Walk"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": day})
    assert r.status_code == 422
    assert error_messages(r) == ["day must be an ISO date in YYYY-MM-DD format"]
    assert client.get(f"/habits/{hid}/checkins").json() == []


@pytest.mark.parametrize("day", ["2026-02-30", "2026-13-01", "2026-00-10"])
def test_checkin_rejects_impossible_date(day):
    hid = client.post("/habits", json={"name": "Journal"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": day})
    assert r.status_code == 422
    assert error_messages(r) == [f"day {day} is not a real calendar date"]
    assert client.get(f"/habits/{hid}/checkins").json() == []


def test_checkin_accepts_leap_day():
    hid = client.post("/habits", json={"name": "Swim"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2028-02-29"})
    assert r.status_code == 200
