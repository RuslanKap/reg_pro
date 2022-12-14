import os
import asyncio
import json
import logging
import time

from aio_pika import connect_robust
from fastapi import FastAPI
from database.db import async_session
from database.models import Posts

app = FastAPI()
RABBIT_HOST = os.getenv('RABBIT_HOST')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -[%(levelname)s]- %(message)s",
)


@app.on_event("startup")
def startup():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main(loop))


@app.get("/")
def read_root():
    return {"Hello": "World"}


async def connect_to_rabbit(loop):
    while True:
        try:
            logging.info("Подключаемся к RabbitMQ...")
            connection = await connect_robust(RABBIT_HOST, loop=loop)
            return connection
        except ConnectionError:
            time.sleep(5)
            logging.warning("Время попытки подключения истекло. Повторная попытка...")


async def main(loop):
    connection = await connect_to_rabbit(loop)
    logging.info("Connected to RabbitMQ!")
    async with connection:
        queue_name = "info"
        channel = await connection.channel()
        queue = await channel.declare_queue(
            queue_name,
            auto_delete=True
        )
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body)
                        logging.info(message.body)
                        session = async_session()
                        post = Posts(**data)
                        session.add(post)
                        await session.commit()
                        await session.close()
                        logging.info("Successfully added new post to the database")
                    except TypeError as er:
                        logging.error(f"Error: {er}", exc_info=True)
                        await session.rollback()
