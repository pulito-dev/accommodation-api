import json
import uuid
import asyncio
from typing import Callable, MutableMapping
from aio_pika import connect, Message, IncomingMessage

class MQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
        
        self.futures: MutableMapping[str, asyncio.Future] = {}


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
        

    async def setup_rpc_queues(self):
        # setup rpc request queues
        accommodations_get_by_id = await self.channel.declare_queue("accommodations.get_by_id.req")
        accommodations_get_by_user_id = await self.channel.declare_queue("accommodations.get_by_user_id.req")
        accommodations_cascade_delete = await self.channel.declare_queue("accommodations.cascade_delete.req")

        # setup rpc response queues
        users_get_by_id = await self.channel.declare_queue("users.get_by_id.res", durable=True)
        listings_cascade_delete = await self.channel.declare_queue("listings.cascade_delete.res", durable=True)
        
        await users_get_by_id.consume(self.rpc_msg_handler)
        await listings_cascade_delete.consume(self.rpc_msg_handler)
    

    async def rpc_msg_handler(self, msg: IncomingMessage):
            # if an exception gets raised, message gets rejected and put back in the queue
            async with msg.process(requeue=True):
                future: asyncio.Future = self.futures.pop(msg.correlation_id, None)
                msg_body = json.loads(
                    msg.body.decode()
                )
                # if future is None, this line throws error and requeues the message
                future.set_result(msg_body)
    
    
    async def send_rpc_message(self, queue: str, message: dict):
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        self.futures[correlation_id] = future

        msg = Message(
            body=json.dumps(message).encode(),
            correlation_id=correlation_id,
            reply_to=f"{queue}.res"
        )

        await self.channel.default_exchange.publish(
            message=msg,
            routing_key=f"{queue}.req"
        )

        return await future
    
    async def send_rpc_response(self, queue: str, message: dict, correlation_id: str):
        msg = Message(
            body = json.dumps(message).encode(),
            correlation_id=correlation_id
        )

        await self.channel.default_exchange.publish(
            message=msg,
            routing_key=f"{queue}.res",
        )


mq_cl = MQClient()
