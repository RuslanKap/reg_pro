import os
import asyncio
import json
import logging
import time

import tornado.ioloop
import tornado.web
from aio_pika import Message, connect_robust

RABBIT_HOST = os.getenv('RABBIT_HOST')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -[%(levelname)s]- %(message)s",
)


class PublisherHandler(tornado.web.RequestHandler):

    def set_default_headers(self) -> None:

        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST")

    async def post(self) -> None:
        try:
            connection = self.application.settings["amqp_connection"]
            channel = await connection.channel()
        except Exception or ConnectionError as ex:
            logging.error(ex)

        try:
            data = {k: v[0].decode("UTF-8") for (k, v) in self.request.body_arguments.items()}
            body = json.dumps(data)
            logging.info(data)
            await channel.default_exchange.publish(
                Message(body=body.encode(), content_type="application/json", ), routing_key="info",
            )
        except ConnectionRefusedError as e:
            logging.error(e)
        finally:
            await channel.close()

        await self.finish(json.dumps({'type': 'success', 'massage': 'Data received'}))


async def connect_to_rabbit():
    while True:
        try:
            logging.info("Подключаемся к RabbitMQ...")
            connection = await connect_robust(RABBIT_HOST)
            return connection
        except ConnectionError:
            time.sleep(5)
            logging.warning("Время попытки подключения истекло. Повторная попытка...")


async def make_app() -> tornado.web.Application:
    amqp_connection = await connect_to_rabbit()
    logging.info("Connected to RabbitMQ!")
    return tornado.web.Application(
        [(r"/publish", PublisherHandler)],
        amqp_connection=amqp_connection,
    )


async def main() -> None:
    app = await make_app()
    app.listen(8888)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
