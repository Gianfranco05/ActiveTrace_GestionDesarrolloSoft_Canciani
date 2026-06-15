import pytest
from app.integrations.moodle_ws import MoodleWSClient


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class DummyClient:
    async def get(self, url, params=None, timeout=None):
        return DummyResponse([
            {"firstname": "Laura", "lastname": "Diaz", "email": "laura@example.com"}
        ])


@pytest.mark.asyncio
async def test_get_enrolled_users_returns_students():
    client = MoodleWSClient("http://moodle", "tok", client=DummyClient())
    students = await client.get_enrolled_users("123")
    assert len(students) == 1
    s = students[0]
    assert s.nombre == "Laura"
    assert s.email == "laura@example.com"
