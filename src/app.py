"""HTTP API сервер на FastAPI (Этап 2).

Реализует 8 обработчиков (Таблица 13), авторизацию RFC 7617 (Basic Auth),
выдачу ответов в формате XML и выполнение вычислений через subprocess.
"""

import argparse
import sys
import subprocess
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dict2xml import dict2xml

from src import data_layer

app = FastAPI(title="Barcode Code128 HTTP API")
security = HTTPBasic()


CONFIG = {
    "username": "admin",
    "password": "secret",
    "test_mode": False,
}


def authenticate(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Проверяет логин и пароль по стандарту RFC 7617 (Basic Auth)."""
    correct_user = credentials.username == CONFIG["username"]
    correct_pass = credentials.password == CONFIG["password"]
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def to_xml_response(data, root_tag: str = "response") -> Response:
    """Преобразует данные Python в XML-ответ с нужным заголовком."""
    if isinstance(data, list):
        payload = {"item": data}
    else:
        payload = data
    xml_content = f"<{root_tag}>\n{dict2xml(payload)}\n</{root_tag}>"
    return Response(content=xml_content, media_type="application/xml")


@app.put("/core/api/submit-user/{key}")
def submit_user(key: int, user: str = Depends(authenticate)):
    """PUT /core/api/submit-user/:key - создание пользователя."""
    row = data_layer.create_user(key=key)
    return to_xml_response(row, root_tag="user")


@app.get("/core/api/discard-user")
def discard_user(key: int, user: str = Depends(authenticate)):
    """GET /core/api/discard-user?key=... - удаление пользователя."""
    try:
        row = data_layer.delete_user(key)
        return to_xml_response(row, root_tag="user")
    except ValueError as err:
        return to_xml_response({"error": str(err)}, root_tag="error")


@app.get("/core/api/browse-user")
def browse_user(user: str = Depends(authenticate)):
    """GET /core/api/browse-user - просмотр списка пользователей."""
    rows = data_layer.get_all_users()
    return to_xml_response(rows, root_tag="users")


def run_barcode_task(arg: str) -> tuple[str, str]:
    """Выполняет генерацию штрих-кода через CLI-утилиту."""
    if CONFIG["test_mode"]:
        return "test_completed", ""

    cmd = [sys.executable, "src/bar.py", "--input", arg]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return "completed", ""
    return "failed", proc.stderr.strip()


@app.put("/core/api/submit-message/{key}")
def submit_message(
    key: int,
    user: int,
    arg: str = "",
    description: str = "",
    tags: str = "",
    stage: str = "",
    auth_user: str = Depends(authenticate),
):
    """PUT /core/api/submit-message/:key"""
    try:
        msg = data_layer.create_message(
            user=user,
            arg=arg,
            description=description,
            tags=tags,
            stage=stage,
            key=key,
        )
        res_text, err_text = run_barcode_task(arg)
        data_layer.create_result(
            message=msg["key"],
            result=res_text,
            stage="final",
            error=err_text,
        )
        return to_xml_response(msg, root_tag="message")
    except ValueError as err:
        return to_xml_response({"error": str(err)}, root_tag="error")


@app.get("/core/api/discard-message")
def discard_message(key: int, auth_user: str = Depends(authenticate)):
    """GET /core/api/discard-message?key=... - удаление сообщения."""
    try:
        row = data_layer.delete_message(key)
        return to_xml_response(row, root_tag="message")
    except ValueError as err:
        return to_xml_response({"error": str(err)}, root_tag="error")


@app.get("/core/api/browse-message/{user}")
def browse_message(user: int, auth_user: str = Depends(authenticate)):
    """GET /core/api/browse-message/:user - сообщения пользователя."""
    rows = data_layer.get_messages_by_user(user)
    return to_xml_response(rows, root_tag="messages")


@app.get("/core/api/browse-result/{message}")
def browse_result(message: int, auth_user: str = Depends(authenticate)):
    """GET /core/api/browse-result/:message - результат сообщения."""
    try:
        row = data_layer.get_result_by_message(message)
        return to_xml_response(row, root_tag="result")
    except ValueError as err:
        return to_xml_response({"error": str(err)}, root_tag="error")


@app.get("/core/api/browse-report")
def browse_report(auth_user: str = Depends(authenticate)):
    """GET /core/api/browse-report - отчет по формуле (13)."""
    rows = data_layer.join()
    return to_xml_response(rows, root_tag="report")


def main() -> None:
    """Точка входа для запуска сервера из командной строки."""
    parser = argparse.ArgumentParser(description="Barcode HTTP API Server")
    parser.add_argument(
        "--username", default="admin", help="Имя пользователя HTTP API"
    )
    parser.add_argument(
        "--password", default="secret", help="Пароль пользователя HTTP API"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Запуск в тестовом режиме без subprocess",
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Порт для запуска сервера"
    )
    args = parser.parse_args()

    CONFIG["username"] = args.username
    CONFIG["password"] = args.password
    CONFIG["test_mode"] = args.test

    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
