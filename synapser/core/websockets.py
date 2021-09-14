import os

from cement.core.log import LogHandler
from twisted.internet import reactor, protocol
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

from synapser.core.data.results import CommandData


class ProcessProtocol(protocol.ProcessProtocol):
    """ I handle a child process launched via reactor.spawnProcess.
    I just buffer the output into a list and call WebSocketProcessOutputterThingFactory.broadcast when
    any new output is read
    """
    def __init__(self, websocket_factory):
        self.ws = websocket_factory
        self.buffer = []

    def outReceived(self, message):
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
        #self.transport.closeStdout()

    def processExited(self, reason):
        print("processExited, status %d" % (reason.value.exitCode,))
        self.transport.closeStdin()

    def processEnded(self, reason):
        print("processEnded, status %d" % (reason.value.exitCode,))
        print("quitting")
        reactor.callFromThread(reactor.stop)


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
        #super(WebSocketProcessOutputterThing, self).connectionLost(self, reason)
        self.factory.unregister(self)


class WebSocketProcessFactory(WebSocketServerFactory):
    """ I maintain a list of connected clients and provide a method for pushing a single message to all of them.
    """
    protocol = WebSocketProcess

    def __init__(self, cmd_data: CommandData, logger: LogHandler, *args, **kwargs):
        WebSocketServerFactory.__init__(self, *args, **kwargs)
        self.clients = []
        self.logger = logger
        self.process = ProcessProtocol(self)
        reactor.spawnProcess(self.process, cmd_data.path, args=cmd_data.args, env=os.environ, path=cmd_data.working_dir,
                             usePTY=False)

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
