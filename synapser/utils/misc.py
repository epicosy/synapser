from pathlib import Path
from typing import List, Dict, AnyStr


def match_patches(sources: List[Path], program_root_dir: Path, patch_root_dir: Path) -> Dict[Path, Path]:
    patch_files = [f.relative_to(patch_root_dir) for f in patch_root_dir.glob("**/*.*")]
    return {(program_root_dir / file): (patch_root_dir / file) for file in sources if file in patch_files}


def args_to_str(args: dict) -> str:
    arg_str = ""

    for opt, arg in args.items():
        if isinstance(arg, dict):
            arg_str += args_to_str(arg)
            continue
        arg_str += f" {opt} {arg}" if arg else f" {opt}"

    return arg_str


def args_to_list(args: dict) -> List[AnyStr]:
    arg_list = []

    for opt, arg in args.items():
        if isinstance(arg, dict):
            arg_list.extend(args_to_list(arg))
            continue

        if arg:
            arg_list.extend([opt, str(arg)])
        else:
            arg_list.append(opt)

    return arg_list
