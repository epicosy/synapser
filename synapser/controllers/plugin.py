from pathlib import Path
from typing import Tuple

from cement import Controller, ex
import yaml


class Plugin(Controller):
    """
        Plugin Controller to handle plugin operations
    """

    class Meta:
        label = 'plugin'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help="Installs plugin",
        arguments=[
            (['-d', '--directory'], {'help': 'Path to the directory with the plugin.', 'required': True, 'type': str})
        ]
    )
    def install(self):
        """
           Sub command for installing the plugin
        """
        plugin_configs, config_file = self.get_plugin_configs()
        plugin_file = self.get_plugin_file()
        # TODO: this might not be the best way to access the name of the plugin
        plugin_name = list(plugin_configs.keys())[0]
        plugin_key = f"plugins.{plugin_name}"

        # TODO: find a better way for doing this
        dest_plugin_file = Path(self.app.get_config('plugin_dir')) / (plugin_file.name.split('.syn.py')[0] + '.py')
        dest_plugin_file = Path(dest_plugin_file.expanduser())
        dest_config_file = Path(self.app.get_config('plugin_config_dir')) / (config_file.name.split('.syn.yml')[0] + '.yml')
        dest_config_file = Path(dest_config_file.expanduser())

        with plugin_file.open(mode="r") as pf, dest_plugin_file.open(mode="w") as dpf:
            self.app.log.info(f"Writing plugin {plugin_file} file to {dest_plugin_file}")
            dpf.write(pf.read())

        with config_file.open(mode="r") as cf, dest_config_file.open(mode="w") as dcf:
            self.app.log.info(f"Writing config file {config_file} file to {dest_config_file}")
            dcf.write(cf.read())

        for file in self.app._meta.config_files:
            path = Path(file)

            if not path.exists():
                continue

            with path.open(mode="r") as stream:
                configs = yaml.safe_load(stream)

                if 'synapser' not in configs:
                    continue

            if plugin_key in configs:
                configs[plugin_key]['enabled'] = True
            else:
                configs[plugin_key] = {'enabled': True}

            with path.open(mode="w") as stream:
                yaml.safe_dump(configs, stream)
                self.app.log.info(f"Updated config file")
                break

    @ex(
        help="Uninstalls plugin",
        arguments=[
            (['-n', '--name'], {'help': 'Name of the plugin.', 'required': True, 'type': str})
        ]
    )
    def uninstall(self):
        """
            Removes plugin and associated files.
        """
        for file in self.app._meta.config_files:
            path = Path(file)

            if not path.exists():
                continue

            with path.open(mode="r") as stream:
                configs = yaml.safe_load(stream)

                if 'synapser' not in configs:
                    continue

            plugin = f"plugins.{self.app.pargs.name}"

            if plugin in configs:
                del configs[plugin]

                # TODO: find a better way for doing this

                plugin_file = Path(self.app.get_config('plugin_dir')) / f"{self.app.pargs.name}.py"
                plugin_file = Path(plugin_file.expanduser())
                config_file = Path(self.app.get_config('plugin_config_dir')) / f"{self.app.pargs.name}.yml"
                config_file = Path(config_file.expanduser())

                if plugin_file.exists():
                    plugin_file.unlink()
                    self.app.log.info(f"{plugin_file} deleted")

                if config_file.exists():
                    config_file.unlink()
                    self.app.log.info(f"{config_file} deleted")

                with path.open(mode="w") as stream:
                    yaml.safe_dump(configs, stream)

                    self.app.log.info(f"removed {plugin} from configs")

                    break
            else:
                self.app.log.warning(f"{plugin} not found.")


    def get_plugin_file(self) -> Path:
        """
            Loads the plugin file
        """

        install_path = self.get_install_path()

        for file in install_path.iterdir():
            if file.name.endswith('.syn.py'):
                self.app.plugin.check(file.name, str(install_path))
                return file

        self.app.log.error("plugin file (*.syn.py) not found")
        exit(1)

    def get_plugin_configs(self) -> Tuple[dict, Path]:
        """
            Gets the configurations for the plugin
        """
        install_path = self.get_install_path()

        for file in install_path.iterdir():
            if file.name.endswith('.syn.yml'):
                with file.open(mode="r") as plugin_stream:
                    return yaml.safe_load(plugin_stream), file

        self.app.log.error("config file (*.syn.yml) not found")
        exit(1)

    def get_install_path(self):
        """
            Returns the path to the install directory
        """
        plugin_path = Path(self.app.pargs.directory)

        if not plugin_path.exists():
            self.app.log.error(f"{plugin_path} not found.")
            exit(1)

        return plugin_path
