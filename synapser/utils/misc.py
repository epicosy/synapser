from pathlib import Path
from typing import List, Dict


def match_patches(sources: List[Path], program_root_dir: Path, patch_root_dir: Path) -> Dict[Path, Path]:
    patch_files = [f.relative_to(patch_root_dir) for f in patch_root_dir.glob("**/*.*")]
    return {(program_root_dir / file): (patch_root_dir / file) for file in sources if file in patch_files}


def args_to_str(args: dict) -> str:
    arg_str = ""

    for opt, arg in args.items():
        if opt == 'args':
            arg_str += f" {arg}"
            continue
        arg_str += f" {opt} {arg}" if arg else f" {opt}"

    return arg_str
