from sqlmodel import Session, create_engine, SQLModel
# TODO: make sure all models are imported here so sqlmodel can form the relationships
from ..models import *

class DBClient():
    def __init__(self):
        self.engine = None
        
    def connect(self, uri: str, connect_args: dict = {}):
        self.engine = create_engine(
            url=uri,
            connect_args=connect_args
        )

    def init_db(self):
        SQLModel.metadata.create_all(self.engine)
    
    def disconnect(self):
        self.engine.dispose()
        self.engine = None


db_cl = DBClient()