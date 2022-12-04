import asyncio
import json

import aio_pika
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import async_session
from database.models import Posts

app = FastAPI()


# Dependency
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


@app.on_event("startup")
def startup():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main(loop))


@app.get("/")
def read_root():
    return {"Hello": "World"}


async def main(loop):
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@rabbitmq:5672/", loop=loop
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
            # Cancel consuming after __aexit__
            async for message in queue_iter:
                async with message.process():
                    print(json.loads(message.body))
                    data = json.loads(message.body)
                    session = async_session()
                    post = Posts(**data)
                    session.add(post)
                    await session.commit()
                    await session.close()

                    # await add_user_post(data, session)
                    if queue.name in message.body.decode():
                        break
