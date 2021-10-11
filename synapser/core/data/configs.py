from dataclasses import dataclass, field
from pathlib import Path
from synapser.utils.misc import args_to_str


@dataclass
class Configs:
    name: str

    def __str__(self):
        return self.name


@dataclass
class ToolConfigs(Configs):
    program: str
    path: str
    args: dict = field(default_factory=lambda: {})
    sanity_check: bool = False
    fault_localization: bool = False

    def validate(self):
        assert Path(self.path).exists(), "Parent path to the executable program not found"
        assert Path(self.path, self.program).exists(), "Executable program for the repair tool not found"

    @property
    def full_path(self):
        return f"{self.path}/{self.program}"

    def __str__(self):
        return f"{self.path}/{self.program} {args_to_str(self.args)}"
