from schema import Schema, And, Use, Optional

from dataclasses import dataclass, field
from pathlib import Path
from synapser.utils.misc import args_to_str


@dataclass
class ToolConfigs:
    """
        Data objects representing the tool's configurations.
    """
    name: str
    program: str
    path: str
    api_cmds: dict = field(default_factory=lambda: {})
    args: dict = field(default_factory=lambda: {})
    sections: dict = field(default_factory=lambda: {})
    help: str = None
    sanity_check: bool = False
    fault_loc: bool = False

    def __getitem__(self, item: str):
        return self.args.get(item, default=None)
    
    def validate(self):
        """
            Checks whether the path and the executable for the tool exist.
        """
        assert Path(self.path).exists(), "Parent path to the executable program not found"
        assert Path(self.path, self.program).exists(), "Executable program for the repair tool not found"
    
    @property
    def help_cmd(self):
        """
            Help command for the repair tool.
        """
        return f"{self.full_path} {self.help}"
    
    @property
    def full_path(self):
        """
            Full path to the repair tool executable.
        """
        return f"{self.path}/{self.program}"

    def __str__(self):
        return f"{self.path}/{self.program} {args_to_str(self.args)}"


def parse_configs(name: str, yaml: dict) -> ToolConfigs:
    """
        Returns the projects in the metadata file.
    """
    sections = Schema(And({str: {'program': str, Optional('args', default={}): dict}}))

    return Schema(And({'program': str, 'path': str, Optional('args', default={}): dict,
                       Optional('api_cmds', default={}): dict, Optional('sections', default={}): sections,
                       Optional('sanity_check', default=False): bool, Optional('fault_loc', default=False): bool,
                       Optional('help', default=None): str},
                      Use(lambda tc: ToolConfigs(name=name, **tc)))).validate(yaml)
