from sqlmodel import Session
from ..core.db  import db_cl
from collections.abc import Generator

def get_db() -> Generator[Session, None, None]:
    with Session(db_cl.engine) as session:
        yield session
