from abc import abstractmethod
from pathlib import Path
from typing import Dict, Union, List

from synapser.core.data.configs import ToolConfigs
from synapser.core.data.results import CommandData, Diff, Patch
from synapser.core.database import Signal
from synapser.handlers.command import CommandHandler


class ToolHandler(CommandHandler):
    class Meta:
        label = 'tool'

    def get_config(self, key: str):
        return self.app.config.get(self.Meta.label, key)

    def get_configs(self, args: dict = None):
        configs = self.app.config.get_section_dict(self.Meta.label).copy()

        if args:
            if 'args' in configs:
                configs['args'].update(args)
            else:
                configs['args'] = args

        return ToolConfigs(name=self.Meta.label, **configs)

    @abstractmethod
    def repair(self, signals: dict, timeout: int, **kwargs) -> CommandData:
        pass

    @abstractmethod
    def help(self) -> CommandData:
        pass

    def get_diff(self, original: Path, patch: Path) -> Diff:
        command_handler = self.app.handler.get('commands', 'command', setup=True)
        command_handler.log = False
        diff_data = command_handler(CommandData(args=f"diff {original} {patch}"))

        return Diff(source_file=original, patch_file=patch, change=diff_data.output)

    def get_patch(self, matches: Dict[Path, Path], is_fix: bool = False) -> Union[Patch, None]:
        if matches:
            return Patch(is_fix=is_fix, diffs=[self.get_diff(original, patch) for original, patch in matches.items()])
        return None
