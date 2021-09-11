
from cement import App, TestApp
from cement.core.exc import CaughtSignal

from synapser.core.interfaces import HandlersInterface
from synapser.handlers.command import CommandHandler
from synapser.handlers.instance import InstanceHandler
from synapser.handlers.api import SignalHandler
from synapser.handlers.plugin import PluginLoader
from .core.exc import SynapserError
from .controllers.base import Base


class Synapser(App):
    """synapser primary application."""

    class Meta:
        label = 'synapser'

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'synapser.ext.database',
            'synapser.ext.server',
            'yaml',
            'colorlog',
            'jinja2',
        ]

        # configuration handler
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        plugin_handler = 'plugin_loader'

        interfaces = [
            HandlersInterface
        ]

        # register handlers
        handlers = [
            Base, CommandHandler, PluginLoader, InstanceHandler, SignalHandler
        ]

    def get_config(self, key: str):
        if self.config.has_section(self.Meta.label):
            if key in self.config.keys(self.Meta.label):
                return self.config.get(self.Meta.label, key)

        return None


class SynapserTest(TestApp, Synapser):
    """A sub-class of Synapser that is better suited for testing."""

    class Meta:
        label = 'synapser'


def main():
    with Synapser() as app:
        try:
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except SynapserError as e:
            print('SynapserError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
