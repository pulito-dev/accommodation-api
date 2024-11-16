import json
from aio_pika import IncomingMessage

async def test_handler(msg: IncomingMessage):
    # if an exeception gets raised, message gets rejected and put beck in the queue
    async with msg.process(requeue=True):
        # msg_text =  json.loads(
        #     msg.body.decode()
        # )

        # txt = msg_text["random_id"]
        # print(f"RECV: {txt}")
        print(msg.body.decode())

        # simulate random failures
        # if random.choice([True, False]):
        #     raise Exception("asdfasdf")