import asyncio

from django.shortcuts import render

import aioamqp
from aiohttp.web import WSMsgType, WebSocketResponse


def index(request):
    return render(request, 'index.html')


@asyncio.coroutine
def socket(request):
    resp = WebSocketResponse()
    yield from resp.prepare(request)

    if 'amqp' not in request.app:
        transport, protocol = yield from aioamqp.connect()
        request.app['amqp'] = protocol

    amqp = request.app['amqp']
    channel = yield from amqp.channel()
    yield from channel.exchange_declare(
        exchange_name='demo-room', type_name='fanout')
    result = yield from channel.queue_declare('', exclusive=True)
    yield from channel.queue_bind(result['queue'], 'demo-room', routing_key='')

    # Consume messages from the queue
    @asyncio.coroutine
    def message(channel, body, envelope, properties):
        if not resp.closed:
            yield from resp.send_str(body.decode('utf-8'))
        yield from channel.basic_client_ack(envelope.delivery_tag)

    yield from channel.basic_consume(message, queue_name=result['queue'])

    # Broadcast messages to the queue
    while True:
        msg = yield from resp.receive()
        if msg.type == WSMsgType.TEXT:
            yield from channel.publish(msg.data, exchange_name='demo-room', routing_key='')
        else:
            break
    # Client requested close
    yield from channel.close()
    return resp
