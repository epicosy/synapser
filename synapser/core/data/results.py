from pathlib import Path
from typing import AnyStr, List, Union
from dataclasses import dataclass
from datetime import datetime

from synapser.core.data.configs import ToolConfigs
from synapser.utils.misc import args_to_list


@dataclass
class Patch:
    is_fix: bool
    source_file: Path
    patch_file: Path
    change: AnyStr

    def __str__(self):
        return f"{self.source_file.name} {self.patch_file.name}\n{self.change}"

    def to_dict(self):
        return {str(self.patch_file): self.change}


@dataclass
class ProcessData:
    args: Union[AnyStr, List] = None
    path: str = ""
    timeout: int = 30
    pid: int = None
    return_code: int = 0
    duration: float = 0
    cwd: str = None
    start: datetime = None
    end: datetime = None
    output: AnyStr = None
    error: AnyStr = None

    def to_dict(self):
        return {'return_code': self.return_code, 'duration': self.duration, 'start': str(self.start),
                'end': str(self.end), 'output': self.output, 'error': self.error, 'timeout': self.timeout}


@dataclass
class CommandData(ProcessData):
    def to_dict(self):
        d = super().to_dict()
        d['args'] = self.args

        return d


@dataclass
class WebSocketData(ProcessData):
    def to_dict(self):
        d = super().to_dict()
        d['args'] = ' '.join(self.args)

        return d


@dataclass
class RepairCommand:
    configs: ToolConfigs
    cwd: Path = None

    def add_arg(self, opt: str, arg):
        self.configs.args[opt] = arg

    def to_list(self):
        return [self.configs.program] + args_to_list(self.configs.args)
