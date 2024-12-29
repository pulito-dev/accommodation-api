from ..core.db  import db_cl
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

async def get_session() -> AsyncSession: # type: ignore

    async_session = sessionmaker(
        db_cl.engine,
        class_=AsyncSession,
        expire_on_commit=True
    )

    async with async_session() as session:
        # return the db session
        yield session

        # close session so queue pool doesn't overflow
        await session.close()
