import asyncio
import json

import tornado.ioloop
import tornado.web
from aio_pika import Message, connect_robust



class Base:
    QUEUE: asyncio.Queue


class PublisherHandler(tornado.web.RequestHandler):

    def set_default_headers(self) -> None:

        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Content-Type", "application/json")

    async def post(self) -> None:

        connection = self.application.settings["amqp_connection"]
        channel = await connection.channel()

        try:
            data = {k: v[0].decode("UTF-8") for (k, v) in self.request.body_arguments.items()}
            body = json.dumps(data)
            await channel.default_exchange.publish(
                Message(body=body.encode(), content_type="application/json", ), routing_key="info",
            )

            print(data)
        finally:
            await channel.close()

        await self.finish(json.dumps({'type': 'success', 'massage': 'Data received'}))


async def make_app() -> tornado.web.Application:
    amqp_connection = await connect_robust(
        "amqp://guest:guest@rabbitmq:5672/"
    )

    channel = await amqp_connection.channel()
    queue = await channel.declare_queue("info", auto_delete=True)
    Base.QUEUE = asyncio.Queue()

    # await queue.consume(Base.QUEUE.put, no_ack=True)

    return tornado.web.Application(
        [(r"/publish", PublisherHandler)],  # (r"/subscribe", SubscriberHandler)],
        amqp_connection=amqp_connection,
    )


async def main() -> None:
    app = await make_app()
    app.listen(8888)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
