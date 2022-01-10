import re

from pathlib import Path
from typing import List, Any, Dict

from synapser.core.data.api import RepairRequest
from synapser.core.data.results import RepairCommand
from synapser.core.database import Signal
from synapser.handlers.tool import ToolHandler
from synapser.utils.misc import match_patches


class GenProg(ToolHandler):
    """GenProg"""

    class Meta:
        label = 'genprog'
        version = 'e720256'

    def repair(self, signals: dict, repair_request: RepairRequest) -> RepairCommand:
        manifest_file = repair_request.working_dir / 'manifest.txt'
        
        with manifest_file.open(mode='w') as mf:
            mf.write('\n'.join(repair_request.manifest))

        self.repair_cmd.add_arg(opt='--program', arg=str(manifest_file))
        self.repair_cmd.add_arg(opt='--prefix', arg=str(repair_request.build_dir))
        self.repair_cmd.add_arg(opt='--rep', arg="cilpatch" if len(repair_request.manifest) > 1 else "c")

        for opt, arg in signals.items():
            self.repair_cmd.add_arg(opt=opt, arg=arg)

        return self.repair_cmd

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

    def parse_extra(self, extra_args: List[str], signal: Signal) -> str:
        """
            Parses extra arguments in the signals.
        """
        return ""


def load(nexus):
    nexus.handler.register(GenProg)
