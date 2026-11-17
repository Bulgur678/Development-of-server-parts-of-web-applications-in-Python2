"""Слой доступа к данным (хранение в памяти).

Таблицы в памяти:
- user: key, datetime
- message: key, datetime, arg, user, description, tags, stage
- result: key, datetime, result, stage, error, message
"""

import time

users: list[dict] = []
messages: list[dict] = []
results: list[dict] = []


def now() -> int:
    """Возвращает текущее время в секундах."""
    return int(time.time())


def get_next_key(table: list[dict]) -> int:
    """Возвращает следующий автоинкрементный ключ для таблицы."""
    if not table:
        return 0
    return max(row["key"] for row in table) + 1


def get_row(table: list[dict], key, name: str) -> dict:
    """Возвращает запись из таблицы по ее ключу."""
    key_int = int(key)
    for row in table:
        if row["key"] == key_int:
            return row
    raise ValueError(f"В таблице '{name}' нет записи с key={key}")


def create_user(key: int) -> dict:
    """Создает новую запись в таблице user."""
    user_key = int(key)
    for user in users:
        if user["key"] == user_key:
            return user
    user = {"key": user_key, "datetime": now()}
    users.append(user)
    return user


def delete_user(key) -> dict:
    """Удаляет запись из таблицы user по ключу."""
    row = get_row(users, key, "user")
    users.remove(row)
    return row


def get_all_users() -> list[dict]:
    """Возвращает список всех пользователей."""
    return users


def create_message(
    user, key, arg="", description="", tags="", stage=""
) -> dict:
    """Создает запись в таблице message для пользователя."""
    owner = get_row(users, user, "user")
    msg_key = int(key)
    for msg in messages:
        if msg["key"] == msg_key:
            return msg
    message = {
        "key": msg_key,
        "datetime": now(),
        "arg": str(arg),
        "user": owner["key"],
        "description": str(description),
        "tags": str(tags),
        "stage": str(stage),
    }
    messages.append(message)
    return message


def delete_message(key) -> dict:
    """Удаляет запись из таблицы message по ключу."""
    row = get_row(messages, key, "message")
    messages.remove(row)
    return row


def get_messages_by_user(user_key) -> list[dict]:
    """Возвращает список сообщений конкретного пользователя."""
    user_int = int(user_key)
    return [msg for msg in messages if msg["user"] == user_int]


def create_result(message, result="", stage="", error="") -> dict:
    """Создает запись в таблице result для сообщения."""
    source = get_row(messages, message, "message")
    row = {
        "key": get_next_key(results),
        "datetime": now(),
        "result": str(result),
        "stage": str(stage),
        "error": str(error),
        "message": source["key"],
    }
    results.append(row)
    return row


def get_result_by_message(message_key) -> dict:
    """Возвращает результат обработки для конкретного сообщения."""
    msg_int = int(message_key)
    for res in results:
        if res["message"] == msg_int:
            return res
    raise ValueError(f"Нет результата для сообщения с key={message_key}")


def join(minutes: int = 7) -> list[dict]:
    """Формирует отчет по формуле (13)."""
    threshold = now() - minutes * 60
    rows = []
    for message in messages:
        if message["datetime"] < threshold:
            continue
        for result in results:
            if result["message"] == message["key"]:
                rows.append(
                    {
                        "tags": message["tags"],
                        "error": result["error"],
                        "result": result["result"],
                    }
                )
    return rows


def clear_database() -> None:
    """Очищает все таблицы базы данных в памяти (для тестов)."""
    users.clear()
    messages.clear()
    results.clear()
