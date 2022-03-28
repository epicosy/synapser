from cement import Controller, ex
from cement.ext.ext_argparse import ArgparseArgumentHandler
from cement.utils.version import get_version_banner

from ..core.exc import SynapserError
from ..core.version import get_version
from ..core.websockets import connect_local_ws_process

VERSION_BANNER = """
Automatic Program Repair API Framework %s
%s
""" % (get_version(), get_version_banner())

argparse_handler = ArgparseArgumentHandler(add_help=False)
argparse_handler.Meta.ignore_unknown_arguments = True


class Base(Controller):
    class Meta:
        label = 'base'

        # text displayed at the top of --help output
        description = 'Automatic Program Repair API Framework'

        # text displayed at the bottom of --help output
        epilog = 'Usage: synapser server'

        # controller level arguments. ex: 'synapser --version'
        arguments = [
            (['-v', '--version'], {'action': 'version', 'version': VERSION_BANNER}),
            (['-vb', '--verbose'], {'help': 'Verbose output.', 'action': 'store_true'})
        ]

    def _default(self):
        """Default action if no sub-command is passed."""

        self.app.args.print_help()

    @ex(
        help='Launches the server API',
        arguments=[
            (['-p', '--port'], {'help': 'Port for server. (Overwrites config port)', 'type': int, 'required': False}),
            (['-a', '--address'], {'help': 'IPv4 host address for server. ', 'type': str, 'default': '0.0.0.0'})
        ]
    )
    def api(self):
        port = self.app.get_config('api_port')

        if self.app.pargs.port:
            port = self.app.pargs.port

        self.app.api.run(debug=True, port=port, host=self.app.pargs.address)

    @ex(
        help='Compile command wrapper',
        arguments=[
            (['--id'], {'help': 'The signal Id.', 'type': int, 'required': True}),
            (['--placeholders'], {'help': 'Placeholders to capture input from the tool.', 'type': str, 'nargs': '+',
                                  'required': False})
        ],
        parents=[argparse_handler]
    )
    def signal(self):
        signal_handler = self.app.handler.get('handlers', 'signal', setup=True)
        signal, data, _ = signal_handler.parse(self.app.pargs.id, self.app.pargs.placeholders, self._parser.unknown_args)
        tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)
        api_handler = tool_handler.register(signal.arg)

        try:
            if not api_handler(signal, data):
                exit(1)
        except SynapserError as se:
            self.app.log.error(str(se))
            exit(1)

        exit(0)

    @ex(
        help='Stream repair instance execution output',
        arguments=[
            (['--id'], {'help': 'The repair instance id.', 'type': int, 'required': True})
        ]
    )
    def stream(self):
        instance_handler = self.app.handler.get('handlers', 'instance', setup=True)
        instance = instance_handler.get(self.app.pargs.id)

        if instance.socket:
            connect_local_ws_process(instance.socket)
        elif instance.status == "done":
            print("WebSocket connection closed")
