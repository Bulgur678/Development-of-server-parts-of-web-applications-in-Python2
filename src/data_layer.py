"""Слой доступа к данным на основе реляционной СУБД SQLite и SQLAlchemy."""

import time
from sqlalchemy import ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATABASE_URL = "sqlite:///barcode_api.db"
REPORT_WINDOW_MINUTES = 7


engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    """Базовый класс декларативных моделей SQLAlchemy."""


class User(Base):
    """ORM-модель таблицы User."""

    __tablename__ = "user"

    key: Mapped[int] = mapped_column(Integer, primary_key=True)
    datetime: Mapped[int] = mapped_column(Integer, nullable=False)

    def to_dict(self) -> dict:
        """Преобразует запись пользователя в словарь."""
        return {"key": self.key, "datetime": self.datetime}


class Message(Base):
    """ORM-модель таблицы Message."""

    __tablename__ = "message"

    key: Mapped[int] = mapped_column(Integer, primary_key=True)
    datetime: Mapped[int] = mapped_column(Integer, nullable=False)
    arg: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.key"), nullable=False
    )
    description: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[str] = mapped_column(String, nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self) -> dict:
        """Преобразует запись сообщения в словарь."""
        return {
            "key": self.key,
            "datetime": self.datetime,
            "arg": self.arg,
            "user": self.user,
            "description": self.description,
            "tags": self.tags,
            "stage": self.stage,
        }


class Result(Base):
    """ORM-модель таблицы Result."""

    __tablename__ = "result"

    key: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    datetime: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[str] = mapped_column(String, nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[int] = mapped_column(
        Integer, ForeignKey("message.key"), nullable=False
    )

    def to_dict(self) -> dict:
        """Преобразует запись результата в словарь."""
        return {
            "key": self.key,
            "datetime": self.datetime,
            "result": self.result,
            "stage": self.stage,
            "error": self.error,
            "message": self.message,
        }


Base.metadata.create_all(engine)


def now() -> int:
    """Возвращает текущее время в секундах."""
    return int(time.time())


def configure_database(url: str) -> None:
    """Переключает подключение БД (используется для изоляции тестов)."""
    global engine
    engine = create_engine(url)
    Base.metadata.create_all(engine)


def clear_database() -> None:
    """Очищает все таблицы в базе данных."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def create_user(key: int) -> dict:
    """Создает новую запись в таблице user или возвращает существующую."""
    user_key = int(key)
    with Session(engine) as session:
        existing = session.get(User, user_key)
        if existing is not None:
            return existing.to_dict()
        user = User(key=user_key, datetime=now())
        session.add(user)
        session.commit()
        return user.to_dict()


def delete_user(key: int) -> dict:
    """Удаляет запись из таблицы user по ключу."""
    user_key = int(key)
    with Session(engine) as session:
        user = session.get(User, user_key)
        if user is None:
            raise ValueError(f"В таблице 'user' нет записи с key={key}")
        data = user.to_dict()
        session.delete(user)
        session.commit()
        return data


def get_all_users() -> list[dict]:
    """Возвращает список всех пользователей."""
    with Session(engine) as session:
        rows = session.scalars(select(User)).all()
        return [row.to_dict() for row in rows]


def create_message(
    user: int,
    arg: str = "",
    description: str = "",
    tags: str = "",
    stage: str = "",
    key: int = 0,
) -> dict:
    """Создает запись в таблице message для существующего пользователя."""
    msg_key = int(key)
    user_key = int(user)
    with Session(engine) as session:
        if session.get(User, user_key) is None:
            raise ValueError(f"В таблице 'user' нет записи с key={user}")
        existing = session.get(Message, msg_key)
        if existing is not None:
            return existing.to_dict()
        message = Message(
            key=msg_key,
            datetime=now(),
            arg=str(arg),
            user=user_key,
            description=str(description),
            tags=str(tags),
            stage=str(stage),
        )
        session.add(message)
        session.commit()
        return message.to_dict()


def delete_message(key: int) -> dict:
    """Удаляет запись из таблицы message по ключу."""
    msg_key = int(key)
    with Session(engine) as session:
        message = session.get(Message, msg_key)
        if message is None:
            raise ValueError(f"В таблице 'message' нет записи с key={key}")
        data = message.to_dict()
        session.delete(message)
        session.commit()
        return data


def get_messages_by_user(user_key: int) -> list[dict]:
    """Возвращает список сообщений конкретного пользователя."""
    user_int = int(user_key)
    with Session(engine) as session:
        stmt = select(Message).where(Message.user == user_int)
        rows = session.scalars(stmt).all()
        return [row.to_dict() for row in rows]


def create_result(
    message: int, result: str = "", stage: str = "", error: str = ""
) -> dict:
    """Создает запись в таблице result для сообщения."""
    msg_key = int(message)
    with Session(engine) as session:
        row = Result(
            datetime=now(),
            result=str(result),
            stage=str(stage),
            error=str(error),
            message=msg_key,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.to_dict()


def get_result_by_message(message_key: int) -> dict:
    """Возвращает результат обработки для конкретного сообщения."""
    msg_int = int(message_key)
    with Session(engine) as session:
        stmt = select(Result).where(Result.message == msg_int)
        row = session.scalars(stmt).first()
        if row is None:
            raise ValueError(
                f"Нет результата для сообщения с key={message_key}"
            )
        return row.to_dict()


def join(minutes: int = REPORT_WINDOW_MINUTES) -> list[dict]:
    """Формирует отчет по формуле (13) через SQL JOIN."""
    threshold = now() - minutes * 60
    with Session(engine) as session:
        stmt = (
            select(Message.tags, Result.error, Result.result)
            .join(Result, Message.key == Result.message)
            .where(Message.datetime >= threshold)
        )
        rows = session.execute(stmt).all()
        return [
            {"tags": tags, "error": error, "result": result}
            for tags, error, result in rows
        ]
