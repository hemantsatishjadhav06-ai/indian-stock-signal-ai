from sqlmodel import SQLModel, create_engine, Session
from .config import settings

connect_args = {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
engine = create_engine(settings.db_url, echo=False, connect_args=connect_args)


def init_db():
    from .trading import paper  # noqa: F401  (register models)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
