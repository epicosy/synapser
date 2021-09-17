import re

from pathlib import Path
from typing import List, Any, Dict

from synapser.core.data.results import CommandData, WebSocketData
from synapser.handlers.tool import ToolHandler
from synapser.utils.misc import match_patches


class GenProg(ToolHandler):
    """GenProg"""

    class Meta:
        label = 'genprog'
        version = 'e720256'

    def help(self) -> CommandData:
        tool_configs = self.get_configs()
        tool_configs.add_arg('--help', '')
        return super().__call__(cmd_data=CommandData(path=tool_configs.full_path, args=tool_configs.to_list(),
                                                     timeout=100))

    def repair(self, signals: dict, timeout: int, working_dir: str, target: str, **kwargs) -> WebSocketData:
        kwargs.update(signals)
        tool_configs = self.get_configs(kwargs)

        return WebSocketData(path=tool_configs.full_path, args=tool_configs.to_list(), cwd=working_dir, timeout=timeout)

    def get_patches(self, working_dir: str, target_files: List[str], **kwargs) -> Dict[str, Any]:
        dirs = [p for p in Path(working_dir).iterdir()]
        dirs.append(Path(working_dir, 'repair'))
        patches = {}

        for tf in target_files:
            patches[tf] = {}

            for d in dirs:
                if d.is_dir() and (re.match(r"^\d{6}$", str(d.name)) or d.name == 'repair'):
                    original, patch_file = match_patches(source=tf, program_root_dir=Path(working_dir, 'sanity'),
                                                         patch_root_dir=d)

                    if patch_file:
                        patch = self.get_patch(original=original, patch=patch_file, is_fix=False)
                        patches[tf][d.name] = patch.change

        return patches


def load(nexus):
    nexus.handler.register(GenProg)
