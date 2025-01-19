import json
from ..client import mq_cl
from sqlalchemy import delete, select
from ...models import Accommodation
from aio_pika import IncomingMessage
from ...routes.deps import get_session
from sqlalchemy.ext.asyncio.session import AsyncSession

async def cascade_delete_handler(msg: IncomingMessage):
    # if an exception gets raised, message gets rejected and put back in the queue
    async with msg.process(requeue=True):
        msg_body = json.loads(
            msg.body.decode()
        )

        user_id = msg_body["user_id"]

        # open session
        session_gen = get_session()
        session: AsyncSession = await anext(session_gen)

        # start transaction
        session.begin()
        try:
            # get all user's accommodations
            statement = select(Accommodation.id).where(Accommodation.user_id == user_id)
            res = await session.scalars(statement)
            accommodations = res.all()

            # delete cascading accommodation
            statement = delete(Accommodation).where(
                Accommodation.user_id==user_id
            )
            await session.execute(statement)
            # raise Exception("SIMULATING ERROR")

            # proceed to delete listings
            res = await mq_cl.send_rpc_message(
                "listings.cascade_delete",
                {
                    "accommodation_id": accommodations
                }
            )

            if not res.get("success"):
                raise Exception()
        except:
            await session.rollback()
            await mq_cl.send_rpc_response("accommodations.cascade_delete",
                {
                    "success": False,
                    "msg": f"Something went wrong."
                },
                msg.correlation_id
            )
        else:
            await session.commit()
            # respond to callback queue
            await mq_cl.send_rpc_response("accommodations.cascade_delete",
                {
                    "success": True,
                    "msg": f"Successfully deleted accommodations with user id {user_id}"
                },
                msg.correlation_id
            )

