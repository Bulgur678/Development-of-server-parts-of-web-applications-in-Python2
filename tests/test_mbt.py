"""Model-Based Testing (MBT) для HTTP API на базе Hypothesis.

Использует RuleBasedStateMachine для генерации последовательностей вызовов
к HTTP API через класс-клиент APIClient и проверки покрытия ветвей.
"""

from fastapi.testclient import TestClient
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule

from src.app import app, CONFIG
from src.client import APIClient

from src.data_layer import clear_database, configure_database


class APIStateMachine(RuleBasedStateMachine):
    """Стейт-машина для фаззинг-тестирования HTTP API по модели."""

    def __init__(self):
        CONFIG["test_mode"] = True
        configure_database("sqlite:///test_mbt.db")
        clear_database()
        self.created_users = set()
        self.created_messages = set()
        super().__init__()
        test_client = TestClient(app)
        self.api_client = APIClient(
            base_url="http://testserver",
            username=CONFIG["username"],
            password=CONFIG["password"],
            client=test_client,
        )
        self.unauth_client = APIClient(
            base_url="http://testserver",
            username="wrong_user",
            password="bad_password",
            client=test_client,
        )

    @rule(key=st.integers(min_value=1, max_value=5))
    def submit_user(self, key: int):
        """Тест создания пользователя: PUT /core/api/submit-user/:key."""
        res = self.api_client.create_user(key)
        assert isinstance(res, dict)
        self.created_users.add(key)

    @rule(key=st.integers(min_value=1, max_value=100))
    def discard_user(self, key: int):
        """Тест удаления пользователя: GET /core/api/discard-user."""
        res = self.api_client.delete_user(key)
        assert isinstance(res, dict)
        self.created_users.discard(key)

    @rule()
    def browse_user(self):
        """Тест просмотра пользователей: GET /core/api/browse-user."""
        users = self.api_client.get_all_users()
        assert isinstance(users, list)

    @rule(
        key=st.integers(min_value=1, max_value=100),
        user_key=st.integers(min_value=1, max_value=100),
        arg=st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
            max_size=10,
        ),
    )
    def submit_message(self, key: int, user_key: int, arg: str):
        """Тест создания сообщения: PUT /core/api/submit-message/:key."""
        if user_key not in self.created_users:
            self.api_client.create_user(user_key)
            self.created_users.add(user_key)

        res = self.api_client.create_message(
            user=user_key,
            arg=arg,
            description="test_desc",
            tags="test_tag",
            stage="new",
            key=key,
        )
        assert isinstance(res, dict)
        self.created_messages.add(key)

    @rule(key=st.integers(min_value=1, max_value=100))
    def discard_message(self, key: int):
        """Тест удаления сообщения: GET /core/api/discard-message."""
        target_key = next(iter(self.created_messages), key)
        res = self.api_client.delete_message(target_key)
        assert isinstance(res, dict)
        self.created_messages.discard(target_key)

    @rule(user_key=st.integers(min_value=1, max_value=100))
    def browse_message(self, user_key: int):
        """Тест сообщений пользователя: GET /core/api/browse-message/:user."""
        msgs = self.api_client.get_messages_by_user(user_key)
        assert isinstance(msgs, list)

    @rule(msg_key=st.integers(min_value=1, max_value=100))
    def browse_result(self, msg_key: int):
        """Тест просмотра результата: GET /core/api/browse-result/:message."""
        res = self.api_client.get_result_by_message(msg_key)
        assert isinstance(res, dict)

    @rule()
    def browse_report(self):
        """Тест итогового отчета: GET /core/api/browse-report."""
        report = self.api_client.join()
        assert isinstance(report, list)

    @rule()
    def test_unauthorized_access(self):
        """Тест проверки авторизации 401 Unauthorized."""
        try:
            self.unauth_client.get_all_users()
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass

    @rule(key=st.integers(min_value=1, max_value=100))
    def submit_message_missing_user(self, key: int):
        """Gри создании сообщения для несуществующего user."""
        res = self.api_client.create_message(user=99, arg="t", key=key)
        assert "error" in res

    @rule()
    def test_old_message_in_report(self):
        """Покрывает ветку отсечения сообщений старше 7 минут в join()."""
        from sqlalchemy import update
        from sqlalchemy.orm import Session
        from src import data_layer

        old_offset_seconds = 600
        with Session(data_layer.engine) as session:
            stmt = update(data_layer.Message).values(
                datetime=data_layer.now() - old_offset_seconds
            )
            session.execute(stmt)
            session.commit()
        report = self.api_client.join()
        assert isinstance(report, list)


TestAPIStateMachine = APIStateMachine.TestCase
