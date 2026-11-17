"""Класс-клиент для взаимодействия с HTTP API (Этап 2).

Имена методов совпадают с методами слоя данных (data_layer.py).
"""

import xml.etree.ElementTree as ET
import httpx


class APIClient:
    """Клиент HTTP API, инкапсулирующий вызовы веб-сервера."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        username: str = "admin",
        password: str = "secret",
        client: httpx.Client | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self._client = client or httpx.Client(
            base_url=self.base_url, auth=self.auth
        )

    def _request(
        self, method: str, path: str, params: dict | None = None
    ) -> dict | list:
        """Отправляет HTTP-запрос и парсит XML-ответ в Python dict/list."""
        url = f"{self.base_url}{path}"
        resp = self._client.request(method, url, params=params, auth=self.auth)

        if resp.status_code == 401:
            raise PermissionError("401 Unauthorized")

        return self._parse_xml(resp.text)

    def _parse_xml(self, xml_text: str) -> dict | list:
        """Простой парсер XML-ответа сервера."""
        root = ET.fromstring(xml_text)
        items = root.findall("item")
        if items:
            result_list = []
            for item in items:
                result_list.append(
                    {child.tag: self._cast_val(child.text) for child in item}
                )
            return result_list

        result_dict = {}
        for child in root:
            result_dict[child.tag] = self._cast_val(child.text)
        return result_dict

    @staticmethod
    def _cast_val(val: str | None):
        """Приводит строковые значения XML к int при возможности."""
        if val is None:
            return ""
        if val.isascii() and val.isdigit():
            return int(val)
        return val

    def create_user(self, key: int) -> dict:
        """Создать пользователя с указанным ключом."""
        res = self._request("PUT", f"/core/api/submit-user/{key}")
        return res if isinstance(res, dict) else {}

    def delete_user(self, key: int) -> dict:
        """Удалить пользователя по ключу."""
        res = self._request("GET", "/core/api/discard-user", {"key": key})
        return res if isinstance(res, dict) else {}

    def get_all_users(self) -> list[dict]:
        """Получить список всех пользователей."""
        res = self._request("GET", "/core/api/browse-user")
        return res if isinstance(res, list) else []

    def create_message(
        self,
        user: int,
        arg: str = "",
        description: str = "",
        tags: str = "",
        stage: str = "",
        key: int = 0,
    ) -> dict:
        """Создать сообщение и выполнить вычислительную задачу."""
        params = {
            "user": user,
            "arg": arg,
            "description": description,
            "tags": tags,
            "stage": stage,
        }
        res = self._request(
            "PUT", f"/core/api/submit-message/{key}", params=params
        )
        return res if isinstance(res, dict) else {}

    def delete_message(self, key: int) -> dict:
        """Удалить сообщение по ключу."""
        res = self._request("GET", "/core/api/discard-message", {"key": key})
        return res if isinstance(res, dict) else {}

    def get_messages_by_user(self, user: int) -> list[dict]:
        """Получить сообщения конкретного пользователя."""
        res = self._request("GET", f"/core/api/browse-message/{user}")
        return res if isinstance(res, list) else []

    def get_result_by_message(self, message: int) -> dict:
        """Получить результат обработки для сообщения."""
        res = self._request("GET", f"/core/api/browse-result/{message}")
        return res if isinstance(res, dict) else {}

    def join(self) -> list[dict]:
        """Получить итоговый отчет по формуле (13)."""
        res = self._request("GET", "/core/api/browse-report")
        return res if isinstance(res, list) else []
