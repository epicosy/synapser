from pathlib import Path
from typing import AnyStr, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Diff:
    source_file: Path
    patch_file: Path
    change: AnyStr

    def __str__(self):
        return f"{self.source_file.name} {self.patch_file.name}\n{self.change}"


@dataclass
class Patch:
    is_fix: bool
    diffs: List[Diff] = field(default_factory=lambda: [])

    def add(self, diff: Diff):
        self.diffs.append(diff)

    def __str__(self):
        return '\n'.join([str(d) for d in self.diffs])


@dataclass
class CommandData:
    # env: dict = None
    args: str
    pid: int = None
    return_code: int = 0
    duration: float = 0
    start: datetime = None
    end: datetime = None
    output: AnyStr = None
    error: AnyStr = None
    timeout: bool = False

    def to_dict(self):
        return {'args': self.args, 'return_code': self.return_code, 'duration': self.duration, 'start': str(self.start),
                'end': str(self.end), 'output': self.output, 'error': self.error, 'timeout': self.timeout}
