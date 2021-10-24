import re

from pathlib import Path
from typing import List, Any, Dict

from synapser.core.data.api import RepairRequest, CoverageRequest
from synapser.core.data.configs import ToolConfigs
from synapser.core.data.results import CommandData, RepairCommand
from synapser.core.database import Signal
from synapser.handlers.tool import ToolHandler
from distutils.dir_util import copy_tree


class MUTAPR(ToolHandler):
    """MUTAPR"""

    class Meta:
        label = 'mut_apr'
        version = '-'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.arg_matches = {'--gcc': '(\d{5}-file.c)',
                            '--bad': '(\d{5}-bad)',
                            '--good': '(\d{5}-good)'
                            }

    def help(self) -> CommandData:
        tool_configs = self.get_configs()
        tool_configs.add_arg('--help', '')
        return super().__call__(cmd_data=CommandData(path=tool_configs.full_path, args=tool_configs.to_list(),
                                                     timeout=100))

    def repair(self, signals: dict, repair_request: RepairRequest) -> RepairCommand:
        # manifest_file = repair_request.working_dir / 'manifest.txt'
        repair_dir = Path(repair_request.working_dir, "repair")
        target_file = Path(repair_request.manifest[0])
        repair_cwd = repair_dir / target_file.parent / target_file.stem
        repair_dir.mkdir(parents=True, exist_ok=True)
        repair_cwd.mkdir(parents=True, exist_ok=True)

        repair_command = RepairCommand(configs=self.get_configs(), cwd=repair_cwd)
        repair_command.add_arg("", str(repair_request.build_dir / target_file))

        for opt, arg in signals.items():
            repair_command.add_arg(opt=opt, arg=f"{arg} --prefix {repair_cwd}")

        return repair_command

    def get_patches(self, working_dir: str, target_files: List[str], **kwargs) -> Dict[str, Any]:
        patches = {}
        repair_dir = Path(working_dir, "repair")

        # TODO: Implement this
        for tf in target_files:
            patches[tf] = {}

        return patches

    def _instrument(self, coverage_request: CoverageRequest, configs: ToolConfigs) -> List[str]:
        inst_path = coverage_request.working_dir / "instrument"
        inst_path.mkdir(parents=True, exist_ok=True)
        inst_files = []

        for file in coverage_request.manifest:
            file = Path(file)
            out_path = inst_path / file.parent

            if not out_path.exists():
                out_path.mkdir()

            out_file = out_path / file.name
            args = ' '.join([f"{opt} {arg}" for opt, arg in configs.sections["coverage"]["args"].items()])
            program = Path(configs.path) / configs.sections["coverage"]["program"]

            with out_file.open(mode="w") as inst_file:
                cmd_data = super().__call__(
                    cmd_data=CommandData(args=f"{program} {args} {coverage_request.build_dir / file}"),
                    cmd_cwd=configs.path)

                if cmd_data.error:
                    continue

                if cmd_data.output and cmd_data.output != '':
                    cmd_data.output = cmd_data.output.replace("fopen(\".//", 'fopen(\"/')
                    inst_file.write(cmd_data.output)
                    inst_files.append(str(out_file))

        return inst_files

    def coverage(self, signals: dict, coverage_request: CoverageRequest):
        inst_files = self._instrument(coverage_request, configs=self.get_configs())

        if inst_files:
            signals['compile'] = signals['compile'].replace("__INST_FILES__", ' '.join(inst_files))
            cmd_data = super().__call__(cmd_data=CommandData(args=signals['compile']))

            if not cmd_data.error:
                # creates folder for coverage files
                cov_dir = coverage_request.working_dir / "coverage"
                cov_dir.mkdir(parents=True, exist_ok=True)

                # insert placeholders
                signals['pos_tests'] = signals['pos_tests'].replace('__COV_OUT_DIR__', str(cov_dir))
                signals['pos_tests'] = signals['pos_tests'].replace('__RENAME_SUFFIX__', '.goodpath')

                super().__call__(cmd_data=CommandData(args=signals['pos_tests']))

                signals['neg_tests'] = signals['neg_tests'].replace('__COV_OUT_DIR__', str(cov_dir))

                super().__call__(cmd_data=CommandData(args=signals['neg_tests']))

                copy_tree(str(cov_dir), str(coverage_request.build_dir))

    def parse_extra(self, extra_args: List[str], signal: Signal) -> str:
        if signal.arg in self.arg_matches:
            args = ' '.join(extra_args)
            path = args.split()[1]
            match = re.search(self.arg_matches[signal.arg], args)

            if match:
                return path + "/" + match.group(0)

        return ""


def load(nexus):
    nexus.handler.register(MUTAPR)
