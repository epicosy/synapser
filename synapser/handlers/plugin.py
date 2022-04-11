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

    def check(self, name: str, path: str):
        """
            Checks if plugin can be loaded
        """
        return super()._load_plugin_from_dir(name, path)

    def _setup(self, app_obj):
        super()._setup(app_obj)

        for section in self.app.config.get_sections():
            try:
                kind, name = section.split('.')

                if kind != 'plugins':
                    continue

                try:
                    self.load_plugin(f"{name}")
                except FrameworkError as fe:
                    raise SynapserError(str(fe))

                loaded = f"{name}" in self._loaded_plugins
                enabled = 'enabled' in self.app.config.keys(section)

                if loaded and enabled:
                    self.tool = name
                    break
            except ValueError:
                continue

        if self.tool is None:
            self.app.log.warning("No plugin loaded.")
