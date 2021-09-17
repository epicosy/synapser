from pathlib import Path
from typing import List, AnyStr, Tuple, Union


def match_patches(source: str, program_root_dir: Path, patch_root_dir: Path) \
        -> Tuple[Path, Union[None, Path]]:
    patch_files = [f.relative_to(patch_root_dir) for f in patch_root_dir.glob("**/*.*")]

    if Path(source) in patch_files:
        return program_root_dir / source, (patch_root_dir / source)

    return program_root_dir / source, None


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
