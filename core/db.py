from ..models import *
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.schema import CreateSchema

class DBClient():
    def __init__(self):
        self.engine = None
        
    def connect(self, uri: str, connect_args: dict = {}):
        self.engine = create_async_engine(
            url=uri,
            connect_args=connect_args,
            # check for conn liveliness before checkout
            pool_pre_ping=True,
            # recycle idle connections younger than 30 mins
            pool_recycle=1800,
            # connection pool size
            pool_size=50,
            # pool overflow size
            max_overflow=75,

            # echo=True,
            future=True
        )

    async def create_schema(self, schema_name: str):
        async with self.engine.begin() as conn:
            await conn.execute(CreateSchema(schema_name, if_not_exists=True))
            await conn.commit()


    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    
    async def disconnect(self):
        await self.engine.dispose()
        self.engine = None


db_cl = DBClient()