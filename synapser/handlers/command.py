import contextlib
import subprocess
import psutil as psutil

from os import environ
from threading import Timer
from datetime import datetime

from autobahn.twisted.websocket import listenWS
from cement import Handler
from twisted.internet import reactor

from synapser.core.exc import CommandError
from synapser.core.data.results import CommandData
from synapser.core.interfaces import HandlersInterface
from synapser.core.websockets import WebSocketProcessFactory


def unbuffered(proc, stream):
    stream = getattr(proc, stream)
    with contextlib.closing(stream):
        while True:
            last = stream.read(100)
            # stop when end of stream reached
            if not last:
                if proc.poll() is not None:
                    break
            else:
                yield last


class CommandHandler(HandlersInterface, Handler):
    class Meta:
        label = 'command'

    def __init__(self, **kw):
        super(CommandHandler, self).__init__(**kw)
        self.log = True

    def _exec(self, proc: subprocess.Popen, cmd_data: CommandData):
        out = []

        cmd = cmd_data.args.split()[0]
        for line in proc.stdout:
            decoded = line.decode()
            out.append(decoded)

            if self.app.pargs.verbose and self.log:
                self.app.log.info(decoded, cmd)

        cmd_data.output = ''.join(out)

        proc.wait(timeout=1)

        if proc.returncode and proc.returncode != 0:
            cmd_data.return_code = proc.returncode
            proc.kill()
            cmd_data.error = proc.stderr.read().decode()

            if cmd_data.error:
                self.app.log.error(cmd_data.error)

    def __call__(self, cmd_data: CommandData, cmd_cwd: str = None, msg: str = None, timeout: int = None,
                 raise_err: bool = False, exit_err: bool = False, **kwargs) -> CommandData:

        if msg and self.app.pargs.verbose:
            self.app.log.info(msg)

        self.app.log.debug(cmd_data.args, cmd_cwd)

        with subprocess.Popen(args=cmd_data.args, shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=environ.copy(), cwd=cmd_cwd) as proc:
            cmd_data.pid = proc.pid
            cmd_data.start = datetime.now()

            if timeout:
                timer = Timer(timeout, _timer_out, args=[proc, cmd_data])
                timer.start()
                self._exec(proc, cmd_data)
                proc.stdout.close()
                timer.cancel()
            else:
                self._exec(proc, cmd_data)

            cmd_data.end = datetime.now()
            cmd_data.duration = (cmd_data.end-cmd_data.start).total_seconds()

            if raise_err and cmd_data.error:
                raise CommandError(cmd_data.error)

            if exit_err and cmd_data.error:
                exit(proc.returncode)

            return cmd_data

    def websocket(self, cmd_data: CommandData, port: int):
        factory = WebSocketProcessFactory(url=f"ws://0.0.0.0:{port}", cmd_data=cmd_data, logger=self.app.log)
        listenWS(factory)
        #reactor.callFromThread(reactor.run)
        reactor.run()


# https://stackoverflow.com/a/54775443
def _timer_out(p: subprocess.Popen, cmd_data: CommandData):
    cmd_data.error = "Command timed out"
    cmd_data.timeout = True
    process = psutil.Process(p.pid)
    cmd_data.return_code = p.returncode if p.returncode else 3

    for proc in process.children(recursive=True):
        proc.kill()

    process.kill()
