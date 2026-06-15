from dataclasses import dataclass

import httpx


@dataclass
class MoodleStudent:
    nombre: str
    apellidos: str
    email: str


class MoodleWSClient:
    def __init__(self, base_url: str, token: str, client: httpx.AsyncClient | None = None):
        self.base_url = base_url
        self.token = token
        self._client = client or httpx.AsyncClient()

    async def get_enrolled_users(self, course_id: str) -> list[MoodleStudent]:
        url = f"{self.base_url}/webservice/rest/server.php"
        params = {"wstoken": self.token, "wsfunction": "core_enrol_get_enrolled_users", "courseid": course_id, "moodlewsrestformat": "json"}
        resp = await self._client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        return [MoodleStudent(nombre=u.get("firstname"), apellidos=u.get("lastname"), email=u.get("email")) for u in data]


class MoodleConnectionError(Exception):
    pass


class MoodleAuthError(Exception):
    pass
