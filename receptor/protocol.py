import asyncio
import logging
import json
from .handler import handle_msg
from .router import router
from receptor import get_node_id, config

logger = logging.getLogger(__name__)


async def create_peer(host, port):
    while True:
        try:
            loop = asyncio.get_event_loop()
            await loop.create_connection(BasicClientProtocol, host, port)
            break
        except Exception:
            print("Connection Refused: {}:{}".format(host, port))
            await asyncio.sleep(5)


async def watch_queue(node, transport):
    buffer_mgr = config.components.buffer_manager
    buffer_obj = buffer_mgr.get_buffer_for_node(node)
    while True:
        if transport.is_closing():
            break
        try:
            msg = buffer_obj.pop()
            transport.write(msg)
        except IndexError:
            pass
        except Exception as e:
            logger.exception("Error received trying to write to {}: {}".format(node, e))
            buffer_obj.push(msg)
            transport.close()
            break
        await asyncio.sleep(1)


def join_router(id_, edges):
    router.register_edge(id_, get_node_id(), 1)
    for edge in json.loads(edges):
        router.register_edge(*edge)


class BasicProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self.greeted = False

    def data_received(self, data):
        logger.info(data)
        loop = asyncio.get_event_loop()
        if not self.greeted:
            self.handshake(data)
        else:
            loop.create_task(handle_msg(data))

    def handshake(self, data):
        data = data.decode("utf-8")
        cmd, id_, edges = data.split(":", 2)
        loop = asyncio.get_event_loop()
        if cmd == "HI":
            self.greeted = True
            logger.debug("Received handshake from client with id %s, responding...", id_)
            self.transport.write(f"HI:{get_node_id()}:{router.get_edges()}".encode("utf-8"))
            join_router(id_, edges)
            loop.create_task(watch_queue(id_, self.transport))
        else:
            logger.error("Handshake failed!")


class BasicClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection to {}'.format(peername))
        self.transport = transport
        self.greeted = False
        logger.debug("Sending handshake to server...")
        self.transport.write(f"HI:{get_node_id()}:{router.get_edges()}".encode("utf-8"))

    def data_received(self, data):
        logger.info(data)
        loop = asyncio.get_event_loop()
        if not self.greeted:
            self.handshake(data)
        else:
            loop.create_task(handle_msg(data))

    def connection_lost(self, exc):
        logger.info('Connection lost with the client...')
        info = self.transport.get_extra_info('peername')
        loop = asyncio.get_event_loop()
        loop.create_task(create_peer(info[0], info[1]))

    def handshake(self, data):
        data = data.decode("utf-8")
        cmd, id_, edges = data.split(":", 2)
        loop = asyncio.get_event_loop()
        if cmd == "HI":
            logger.debug("Received handshake from server with id %s", id_)
            self.greeted = True
            join_router(id_, edges)
            loop.create_task(watch_queue(id_, self.transport))
        else:
            logger.error("Handshake failed!")
