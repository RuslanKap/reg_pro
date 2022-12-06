import os
import asyncio
import json
import logging

import pytest_asyncio
import pytest
import tornado.ioloop
import tornado.web
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from aio_pika import Message, connect_robust

from backend.main import make_app, PublisherHandler, RABBIT_HOST


def test_rabbit_host_variable_set():
    assert os.getenv('RABBIT_HOST') is not None, 'RABBIT_HOST environment variable is not set'


@pytest.mark.asyncio
async def test_make_app():
    app = await make_app()
    assert isinstance(app, tornado.web.Application)
    assert 'amqp_connection' in app.settings
    assert app.settings['amqp_connection'] is not None


@pytest.mark.asyncio
async def test_publisher_handler_post_request():
    amqp_connection = await connect_robust(RABBIT_HOST)
    channel = await amqp_connection.channel()
    await channel.declare_queue("info", auto_delete=True)

    app = tornado.web.Application(
        [(r"/publish", PublisherHandler)],
        amqp_connection=amqp_connection,
    )
    request = tornado.httpclient.HTTPRequest(
        url='http://localhost:8888/publish',
        method='POST',
        body='{"key1": "value1", "key2": "value2"}'
    )
    client = tornado.httpclient.AsyncHTTPClient()
    response = await client.fetch(request)

    assert response.code == 200
    assert json.loads(response.body) == {'type': 'success', 'massage': 'Data received'}
