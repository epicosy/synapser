import requests

from cement import Controller, ex
from cement.utils.version import get_version_banner
from ..core.version import get_version


VERSION_BANNER = """
Automatic Program Repair API Framework %s
%s
""" % (get_version(), get_version_banner())


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
            (['--id'], {'help': 'The signal Id.', 'type': int, 'required': True})
        ]
    )
    def signal(self):
        signal_handler = self.app.handler.get('handlers', 'signal', setup=True)

        signal = signal_handler.load(self.app.pargs.sid)
        response = requests.post(signal.url, json=signal.decoded())

        if response.status_code != 200:
            exit(1)
        if 'error' in response.json() and response.json()['error'] is not None:
            exit(1)

        exit(0)
