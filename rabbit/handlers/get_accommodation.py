import json
from ..client import mq_cl
from sqlmodel import select
from ...models import Accommodation
from aio_pika import IncomingMessage
from ...routes.deps import get_session
from sqlalchemy.ext.asyncio.session import AsyncSession


async def get_accommodation_handler(msg: IncomingMessage):
    async with msg.process(requeue=True):
        msg_body = json.loads(
            msg.body.decode()
        )

        accommodation_id = msg_body["accommodation_id"]

        session_gen = get_session()
        session: AsyncSession = await anext(session_gen)

        accommodation = await session.get(Accommodation, accommodation_id)

        # serialize the body
        if not accommodation:
            accommodation = {}
        else: 
            accommodation = accommodation.model_dump()

        await mq_cl.send_rpc_response("accommodations.get_by_id",
            { "data": accommodation },
            msg.correlation_id
        )