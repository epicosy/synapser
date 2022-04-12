import asyncio
import functools
import os
import time
from collections import Callable

from twisted.internet import protocol
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, \
    WebSocketClientProtocol, WebSocketClientFactory
from cement.core.log import LogHandler
from twisted.internet.asyncioreactor import AsyncioSelectorReactor
from twisted.internet.defer import ensureDeferred

from synapser.core.data.results import WebSocketData


def ensure_deferred(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)
        return ensureDeferred(result)

    return wrapper


class ProcessProtocol(protocol.ProcessProtocol):
    """ I handle a child process launched via reactor.spawnProcess.
    I just buffer the output into a list and call WebSocketProcessFactory.broadcast when
    any new output is read
    """

    def __init__(self, websocket_factory):
        self.ws = websocket_factory
        self.buffer = []

    def outReceived(self, message):
        print("Log: %s" % message)
        self.ws.broadcast(message)
        self.buffer.append(message)
        # Last 10 messages please
        self.buffer = self.buffer[-10:]

    def errReceived(self, data):
        print("Error: %s" % data)

    def inConnectionLost(self):
        print("inConnectionLost! stdin is closed! (we probably did it)")

    def outConnectionLost(self):
        print("outConnectionLost! The child closed their stdout!")
        # self.transport.closeStdout()

    def processExited(self, reason):
        if reason.value.exitCode:
            print("processExited, status %d" % (reason.value.exitCode,))
        self.transport.closeStdin()

    def processEnded(self, reason):
        if reason.value.exitCode:
            print("processEnded, status %d" % (reason.value.exitCode,))
        print("quitting")
        self.transport.loseConnection()
        self.ws.reactor.callFromThread(self.ws.reactor.stop)
        self.ws.finish(self.ws.rid)
        self.ws.loop.stop()
#        self.ws.loop.close()


# https://autobahn.ws/python
class WebSocketProcess(WebSocketServerProtocol):
    """ I handle a single connected client. We don't need to do much here, simply call the register and un-register
    functions when needed.
    """

    def onOpen(self):
        self.factory.register(self)
        for line in self.factory.process.buffer:
            self.sendMessage(line)

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        # super(WebSocketProcessOutputterThing, self).connectionLost(self, reason)
        self.factory.unregister(self)


class WebSocketProcessFactory(WebSocketServerFactory):
    """ I maintain a list of connected clients and provide a method for pushing a single message to all of them.
    """
    protocol = WebSocketProcess

    def __init__(self, ws_data: WebSocketData, rid: int, finish: Callable, logger: LogHandler, *args, **kwargs):
        WebSocketServerFactory.__init__(self, *args, **kwargs)
        self.clients = []
        self.logger = logger
        self.process = ProcessProtocol(self)
        self.finish = finish
        self.rid = rid
        self.ws_data = ws_data

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.reactor = AsyncioSelectorReactor()
        self.listener = self.reactor.listenTCP(0, self)
        self.reactor.callFromThread(self.reactor.startRunning, False)
        self.logger.debug(self.ws_data.args)
        self.reactor.spawnProcess(self.process, self.ws_data.path, args=self.ws_data.args, env=os.environ,
                                  path=self.ws_data.cwd, usePTY=False)

    def run(self):
        self.loop.run_forever()

    def register(self, client):
        self.logger.info("Registered client %s" % client)
        if client not in self.clients:
            self.clients.append(client)

    def unregister(self, client):
        self.logger.info("Unregistered client %s" % client)
        if client in self.clients:
            self.clients.remove(client)

    def broadcast(self, message):
        for client in self.clients:
            client.sendMessage(message)


class WebClientProcess(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onConnecting(self, transport_details):
        print("Connecting; transport details: {}".format(transport_details))
        return None  # ask for defaults

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print(payload)
        else:
            print(payload.decode('utf8'))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        self.transport.loseConnection()
        raise KeyboardInterrupt


def connect_local_ws_process(port):
    reactor = AsyncioSelectorReactor()
    factory = WebSocketClientFactory(f"ws://127.0.0.1:{port}")
    factory.protocol = WebClientProcess

    try:
        reactor.connectTCP("127.0.0.1", port, factory)
        reactor.run()
    except KeyboardInterrupt:
        pass
    finally:
        reactor.stop()
