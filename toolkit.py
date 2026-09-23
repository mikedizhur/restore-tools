from pathlib import Path
import hashes as hs
import fileops as fo
from sorter import GetFileType


def MakePath(path):
    if isinstance(path, Path):
        return path
    return Path(path)


def SmartGetHashes(*args, **kwargs):
    assert len(args) >= 1
    if len(args) == 1:
        path = Path(args[0])
        assert path.exists()
        # 1 file
        if path.is_file():
            if "sep" in kwargs:
                sep = kwargs["sep"]
            else:
                sep = ":"

            return hs.SelectDuplicates(hs.LoadHashes(path))

        # 1 directory
        if path.is_dir():
            options = {
                "recursive": True,
                "form": "hashes",
                "out": None,
                "outonly": False,
                "overwrite": True,
                "sep": ":",
            }

            for key in options:
                if key in kwargs:
                    options[key] = kwargs[key]

            return hs.GetHashes(path, **options)

    if len(args) == 2:
        old, new = Path(args[0]), Path(args[1])

        # 2 directories
        if old.is_dir() and new.is_dir():
            options = {"recursive_old": True, "recursive_new": True}
            for key in options:
                if key in kwargs:
                    options[key] = kwargs[key]

            return hs.GetONHashesFromPaths(old, new, **options)

        hashes_old = None
        hashes_new = None
        if old.is_file():
            hashes_old = hs.LoadHashes(old)
        if old.is_dir():
            hashes_old = hs.GetHashes(old)
        if new.is_file():
            hashes_new = hs.LoadHashes(new)
        if new.is_dir():
            hashes_new = hs.GetHashes(new)

        assert (
            hashes_old is not None and hashes_new is not None
        ), "Not a file or directory provided"

        return hs.GetONHashesFromHashes(hashes_old, hashes_new)

    return None


# def DeduplicateDirectory(path: Path, dry=False, shortest=True):
#     path = MakePath(path)
#     paths = hs.PathsFromHashes(hs.SelectDuplicates(hs.GetHashes(path), shortest=shortest))
#     if not dry:
#         for p in paths.keys():
#             fo.FileDelete(MakePath(p))
#     return paths


def DeduplicateDirectory(
    path: Path = None,
    hashes=None,
    dry=False,
    fastest=False,
    shortest=True,
    operation=fo.FileDelete,
):
    """Use hashes with fast ONLY if you intend on deleting ALL of the hashed files"""

    assert not (path is None and hashes is None), "provide path or hashes"
    if path is not None:
        path = MakePath(path)

    failed = []

    if fastest:
        if hashes is None:
            hashes = hs.GetHashes(path, dupe_only=True)
        if not dry:
            for paths in hashes.values():
                for p in paths:
                    if not operation(MakePath(p)):
                        failed.append(p)
        return hashes, failed

    if hashes is None:
        paths = hs.PathsFromHashes(
            hs.SelectDuplicates(hs.GetHashes(path), shortest=shortest)
        )
    else:
        paths = hs.PathsFromHashes(hs.SelectDuplicates(hashes, shortest=shortest))

    if not dry:
        for p in paths.keys():
            if operation(MakePath(p)):
                failed.append(p)

    return paths, failed


def DeduplicateNew(*args, **kwargs):
    """
    nondestructive = False
    operation = fo.FileDelete
    """
    assert 1 <= len(args) <= 2, "Provide duplicates variable or paths/hashes"
    dupes = None
    if len(args) == 1:
        assert isinstance(args[0], dict) and isinstance(
            args[0].values()[0], dict
        ), "Variable must be in duplicates format"
        dupes = args[0]
    else:
        options = {"nondestructive": False}
        for key in kwargs:
            if key in options:
                options[key] = kwargs[key]
        dupes = SmartGetHashes(
            args[0], args[1], nondestructive=options["nondestructive"]
        )

    assert dupes is not None

    operation = fo.FileDelete
    if "operation" in kwargs:
        operation = kwargs["operation"]

    failed = []

    for d in dupes.values():
        for path in d["new"]:
            if operation(path):
                # debug info
                failed.append(path)
    return failed


def FileSortMover(path: Path, outpath: Path, extended=True, other=True):
    ext = GetFileType(path, extended=extended)
    out = Path(outpath / ext)

    if not out.exists():
        Path(outpath / ext).mkdir()

    fo.FileMove(path, out)
    return 0


def SortFiles(
    outpath: Path,
    hashes=None,
    paths=None,
    extended_sort=True,
    types_only=False,
    type_actions=None,
):
    # generate dict of unique extensions and (action, dir)
    # go over each file and perform the op

    outpath = MakePath(outpath)
    if outpath.exists():
        assert outpath.is_dir()
    else:
        outpath.mkdir()

    if paths is None:
        pass
    elif isinstance(paths, list):
        for f in paths:
            FileSortMover(MakePath(f), outpath, extended_sort)
    elif isinstance(paths, dict):
        for f in paths.keys():
            FileSortMover(MakePath(f), outpath, extended_sort)
    elif isinstance(paths, Path) or isinstance(paths, str):
        d = Path(paths).rglob("*")
        for f in d:
            if f.is_file():
                FileSortMover(MakePath(f), outpath, extended_sort)

    if hashes is not None:
        for h in hashes:
            for f in hashes[h]:
                FileSortMover(MakePath(f), outpath, extended_sort)

    return 0


def CleanupDirectories(path: Path):
    return fo.DirectoryCleanup(MakePath(path), recursive=True)


def ChangeExtensions():
    pass


# def OperateHashes(hashes: dict, operation="move"):
#     pass


# def WriteDuplicatesOld():
#     pass
#
# def WriteDuplicatesNew():
#     pass
