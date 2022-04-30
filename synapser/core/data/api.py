from pathlib import Path
from typing import AnyStr, List
from dataclasses import dataclass


@dataclass
class RepairRequest:
    args: dict
    iid: int
    manifest: List[AnyStr]
    working_dir: Path
    build_dir: Path
    timeout: int


@dataclass
class CoverageRequest:
    manifest: List[AnyStr]
    working_dir: Path
    build_dir: Path
