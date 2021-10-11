from pathlib import Path
from typing import AnyStr, List
from dataclasses import dataclass


@dataclass
class RepairRequest:
    args: dict
    manifest: List[AnyStr]
    working_dir: Path
    build_dir: Path
    timeout: int
