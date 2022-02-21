import os
import re

from pathlib import Path
from typing import List, Any, Dict

from synapser.core.data.api import RepairRequest
from synapser.core.data.results import RepairCommand
from synapser.core.database import Signal
from synapser.handlers.tool import ToolHandler
from synapser.utils.misc import match_patches


class Arja(ToolHandler):
    """GenProg"""

    class Meta:
        label = 'arja'
        version = 'xyz'

    def repair(self, signals: dict, repair_request: RepairRequest) -> RepairCommand:
        repair_args = repair_request.args
        src = repair_args.get('src')
        src_class = repair_args.get('src_class')
        test_class = repair_args.get('test_class')
        classpath = repair_args.get('classpath')
        perfect_fl_dir = repair_args.get('perfect_fl_dir')
        test_cmd = repair_args.get('test_cmd')

        self.repair_cmd.add_arg('-DtestFiltered', 'false')
        self.repair_cmd.add_arg('-DdiffFormat', 'true')
        self.repair_cmd.add_arg('-Dseed', '0')

        self.repair_cmd.add_arg('-DprojectDir', repair_request.working_dir)
        self.repair_cmd.add_arg('-DsrcJavaDir', src)
        self.repair_cmd.add_arg('-DbinJavaDir', src_class)
        self.repair_cmd.add_arg('-DbinTestDir', test_class)
        self.repair_cmd.add_arg('-Ddependences', classpath)

        self.repair_cmd.add_arg('-DgzoltarDataDir', perfect_fl_dir)
        self.repair_cmd.add_arg('-DrunTestCommand', test_cmd)

        return self.repair_cmd

    def get_patches(self, working_dir: str, target_files: List[str], **kwargs) -> Dict[str, Any]:
        # Borrowed from RepairThemAll
        patches_folder = None
        for d in os.listdir(working_dir):
            if "patches_" in d:
                patches_folder = d
                break
        patches = {"patches": []}

        path_results = os.path.join(working_dir, patches_folder) if patches_folder is not None else None
        if path_results is not None and os.path.exists(path_results):
            for f in os.listdir(path_results):
                path_f = os.path.join(path_results, f)
                if not os.path.isfile(path_f) or ".txt" not in f:
                    continue
                patch = {
                    "edits": []
                }
                diff_path = os.path.join(path_f.replace(".txt", ""), "diff")
                if os.path.exists(diff_path):
                    with open(diff_path) as fd:
                        patch["patch"] = fd.read()
                with open(path_f) as fd:
                    str_patches = fd.read().split(
                        "**************************************************")
                    for str_patch in str_patches:
                        splitted_patch = str_patch.strip().split("\n")
                        info_line = splitted_patch[0].split(" ")
                        if info_line[0] == "Evaluations:" or "EstimatedTime:" == info_line[0]:
                            continue

                        is_kali = "." in info_line[-1]
                        if not is_kali:
                            edit = {
                                "type": info_line[1],
                                "path": " ".join(info_line[2:-1]).replace("%s/" % working_dir, ""),
                                "line": int(info_line[-1])
                            }
                            content = "%s\n" % splitted_patch[2]
                            for line in splitted_patch[3:]:
                                if line == "Seed:":
                                    edit["faulty"] = content.strip()
                                    content = ""
                                else:
                                    content += "%s\n" % line
                            edit["seed"] = content.strip()
                        else:
                            edit = {
                                "type": "%s %s" % (info_line[0], info_line[1]),
                                "path": " ".join(info_line[2:-2]).replace("%s/" % working_dir, ""),
                                "line": int(info_line[-2]),
                                "faulty": "\n".join(splitted_patch[1:])
                            }

                        patch['edits'].append(edit)
                patches["patches"].append(patch)

        return patches

    def parse_extra(self, extra_args: List[str], signal: Signal) -> str:
        """
            Parses extra arguments in the signals.
        """
        return ""


def load(nexus):
    nexus.handler.register(Arja)
