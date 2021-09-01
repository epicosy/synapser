import re
from pathlib import Path
from typing import List, Union

from synapser.core.data.results import CommandData
from synapser.core.data.results import Patch
from synapser.handlers.tool import ToolHandler
from synapser.utils.misc import match_patches


class GenProg(ToolHandler):
    """GenProg"""
    class Meta:
        label = 'genprog'
        version = 'e720256'

    def help(self) -> CommandData:
        tool_configs = self.get_configs(args={'--help': ''})
        return super().__call__(cmd_data=CommandData(args=str(tool_configs)))

    def repair(self, compiler_command: str, test_command: str, timeout: int, **kwargs) -> CommandData:
        args = {"--compiler-command": compiler_command, "--test-command": test_command}
        args.update(kwargs)
        tool_configs = self.get_configs(args)
        cmd_data = super().__call__(cmd_data=CommandData(args=str(tool_configs)), timeout=timeout)

        return cmd_data

    def get_patches(self, working_dir: Path, target_files: List[Path], **kwargs) -> List[Patch]:
        patches = []

        for d in self.iterdir(working_dir):
            if d.is_dir() and re.match(r"^\d{6}$", str(d.name)):
                matches = match_patches(sources=target_files, program_root_dir=working_dir / 'sanity',
                                        patch_root_dir=d)
                patch = self.get_patch(matches=matches, is_fix=False)

                if patch:
                    patches.append(patch)

        return patches

    def get_fix(self, working_dir: Path, target_files: List[Path], **kwargs) -> Union[Patch, None]:
        repair_dir = working_dir / Path("repair")

        if repair_dir.exists():
            return None

        matches = match_patches(sources=target_files, program_root_dir=working_dir / 'sanity',
                                patch_root_dir=repair_dir)

        return self.get_patch(matches=matches, is_fix=True)


def load(nexus):
    nexus.handler.register(GenProg)
