from cement.core.exc import FrameworkError
from cement.ext.ext_plugin import CementPluginHandler

from synapser.core.exc import SynapserError


class PluginLoader(CementPluginHandler):
    class Meta:
        label = 'plugin_loader'

    def __init__(self):
        super().__init__()
        self._tool = None

    @property
    def tool(self):
        return self._tool

    @tool.setter
    def tool(self, name: str):
        self._tool = name

    def _setup(self, app_obj):
        super()._setup(app_obj)

        for section in self.app.config.get_sections():
            try:
                _, kind, name = section.split('.')

                if kind != 'tool':
                    continue

                try:
                    self.load_plugin(f"{kind}/{name}")
                except FrameworkError as fe:
                    raise SynapserError(str(fe))

                loaded = f"{kind}/{name}" in self._loaded_plugins
                enabled = 'enabled' in self.app.config.keys(section)

                if loaded and enabled:
                    self.tool = name
                    break
            except ValueError:
                continue
