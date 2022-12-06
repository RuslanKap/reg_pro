import os
import asyncio
import json
import logging

import aio_pika
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


async def main(loop):
    connection = await aio_pika.connect_robust(
        # "amqp://guest:guest@rabbitmq:5672/", loop=loop
        RABBIT_HOST, loop=loop
    )

    async with connection:
        queue_name = "info"

        # Creating channel
        channel = await connection.channel()

        # Declaring queue
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
                    if queue.name in message.body.decode():
                        break
