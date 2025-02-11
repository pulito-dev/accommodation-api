from .core.db import db_cl
from fastapi import FastAPI
from .core.config import config
from .rabbit.client import mq_cl
from contextlib import asynccontextmanager

from .rabbit.handlers.cascade_delete import cascade_delete_handler
from .rabbit.handlers.get_accommodation import get_accommodation_handler
from .rabbit.handlers.get_user_accommodations import get_user_accommodations


@asynccontextmanager
async def lifespan(_: FastAPI):
    # everything before yield is executed before the app starts up
    # set up rabbit
    await mq_cl.connect(str(config.RABBIT_URI))
    await mq_cl.setup_rpc_queues()
    await mq_cl.consume("accommodations.cascade_delete.req", cascade_delete_handler)
    await mq_cl.consume("accommodations.get_by_id.req", get_accommodation_handler)
    await mq_cl.consume("accommodations.get_by_user_id.req", get_user_accommodations)   

    # set up db
    db_cl.connect(str(config.DB_URI))
    await db_cl.create_schema(str(config.DB_SCHEMA))

    # create tables
    await db_cl.init_db()

    yield
    
    # everything after yield is execute after the app shuts down
    await mq_cl.disconnect()
    await db_cl.disconnect()


app = FastAPI(
    title=config.TITLE,
    lifespan=lifespan
)


from .routes.accommodations import accommodation_router


app.include_router(accommodation_router, prefix="/accommodations")


# @app.api_route("/")
# async def home():
#     txt = "".join(random.choices(string.ascii_letters, k=4))
#     await mq_cl.send_message("accommodations", {
#         "random_id": txt
#     })
#     print(f"SENT: {txt}")

#     return {
#         "hello": "world"
#     }
