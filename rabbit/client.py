import json
from typing import Callable
from aio_pika import connect, Message, IncomingMessage

class MQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None


    async def connect(self, uri: str):
        self.connection = await connect(uri)
        self.channel = await self.connection.channel(publisher_confirms=False)


    async def disconnect(self):
        if not self.channel.is_closed:
            await self.channel.close()
        if not self.connection.is_closed:
            await self.connection.close()


    def is_connected(self):
        if self.connection.is_closed or self.channel.is_closed:
            return False
        return True


    async def consume(self, queue_name: str, callback: Callable[[IncomingMessage], None]):
        self.queue = await self.channel.declare_queue(queue_name)

        await self.queue.consume(
            callback=callback,
            # https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/2-work-queues.html#message-acknowledgment
            no_ack=False
        )
        
        print(f"started consuming queue {queue_name}")


    async def send_message(self, queue: str, message: dict):
        """Usage Example
        ```
        await send_message({"asdf": "asdf"})
        ```
        """
        
        async with self.channel.transaction():
            msg = Message(
                body = json.dumps(message).encode()
            )

            await self.channel.default_exchange.publish(
                message=msg,
                routing_key=queue
            )
    

mq_cl = MQClient()
