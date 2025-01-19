import json
from ..client import mq_cl
from sqlmodel import select
from ...models import Accommodation
from aio_pika import IncomingMessage
from ...routes.deps import get_session
from sqlalchemy.ext.asyncio.session import AsyncSession


async def get_user_accommodations(msg: IncomingMessage):
    async with msg.process(requeue=True):
        msg_body = json.loads(
            msg.body.decode()
        )

        user_id = msg_body["user_id"]

        session_gen = get_session()
        session: AsyncSession = await anext(session_gen)

        statement = select(Accommodation.id).where(Accommodation.user_id == user_id)
        res = await session.scalars(statement)
        accommodations = res.all()

        # serialize the body

        await mq_cl.send_rpc_response("accommodations.get_by_user_id",
            { "data": accommodations },
            msg.correlation_id
        )