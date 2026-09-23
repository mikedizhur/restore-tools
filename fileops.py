from pathlib import Path


def FileRename(path: Path) -> Path:
    name = path.name.split(".")
    parent = path.parents[0]
    if len(name) == 1 or (len(name) == 2 and len(name[0]) == 0):
        name.append("1")
    elif name[-1].isdigit():
        name[-1] = str(int(name[-1]) + 1)
    # Is it redundant?
    elif len(name) == 2:
        name = [name[0], "1", name[1]]
    else:
        if name[-2].isdigit():
            name[-2] = str(int(name[-2]) + 1)
        else:
            name = [*name[:-1], "1", name[-1]]
    return parent / ".".join(name)


def FileMove(src: Path, dst: Path, rename=True):
    if dst.is_dir():
        dst = dst / src.name
    if not rename and dst.exists():
        return 1
    while dst.exists():
        dst = FileRename(dst)
    src.move(dst)
    return 0


def FileDelete(path: Path):
    path.unlink()
    return 0


def FileCopy(src: Path, dst: Path, rename=True):
    if Path(dst).is_dir():
        dst = dst / src.name
    if not rename and dst.exists():
        return 1
    while dst.exists():
        dst = FileRename(dst)
    src.copy(dst)
    return 0


def DirectoryCleanup(path: Path, recursive=True):
    assert path.is_dir()
    empty = True
    for item in path.iterdir():
        if item.is_dir():
            if not recursive:
                return 1
            if DirectoryCleanup(item):
                empty = False
        elif item.is_file():
            empty = False
    if empty:
        path.rmdir()
        return 0
    return 1
