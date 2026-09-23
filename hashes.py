from hashlib import file_digest
from pathlib import Path


def GetHash(p, alg="md5") -> str:
    """
    Gets hash of a file from path
    """
    if type(p) is str:
        p = Path(p)
    assert p.is_file()
    with open(p, "rb") as f:
        digest = file_digest(f, alg).hexdigest()
    return digest


def GetHashes(
    d: Path,
    recursive=True,
    form="hashes",
    out=None,
    outonly=False,
    overwrite=True,
    sep=":",
    dupe_only=False,
):
    """
    Hashes every file in a directory
    form is either 'hashes' or 'files'.
        'hashes' -> standard hash form {hash1:[file1, file2], hash2:[file1, file2]}
        'files'  -> {file1:hash1, file2:hash2}
    """
    assert d.is_dir()

    if recursive:
        d = Path(d).rglob("*")
    else:
        d = Path(d).iterdir()

    hashes = {}

    write_to_file = False
    if out is not None:
        out = Path(out)
        assert out.is_file()
        write_to_file = True
        if overwrite:
            dump = open(out, "w")
            dump.write("")
            dump.close()
        dump = open(out, "a")

    for f in d:
        f = f.absolute()
        if not f.is_file():
            continue

        h = GetHash(f)

        if write_to_file:
            dump.write(f"{str(f.absolute())}{sep}{str(h)}\n")
        if not outonly:
            match form:
                case "files":
                    hashes[f.absolute()] = h
                case "hashes":
                    if h in hashes:
                        hashes[h].append(f)
                    else:
                        hashes[h] = [f] if not dupe_only else []

    if write_to_file:
        dump.close()

    return hashes


def RemoveNonDuplicatesON(hashes: dict, nondestructive=True):
    if nondestructive:
        hashes = hashes.copy()

    for h in list(hashes.keys()):
        if len(hashes[h]["new"]) == 0:
            hashes.pop(h)

    return hashes


def GetONHashesFromPaths(
    old: Path, new: Path, recursive_old=True, recursive_new=True
) -> dict:
    """
    Find duplicates via comparing hashes in 2 directories
    """
    # {old:[] new:[]}
    # old {hash : [file1, file2]}
    # new {hash : [file1, file2]}

    hashes = dict()

    if recursive_old:
        d = old.rglob("*")
    else:
        d = old.iterdir()

    for f in d:
        if f.is_file():
            h = GetHash(f)
            if h in hashes:
                hashes[h]["old"].append(f.absolute())
            else:
                hashes[h] = {"old": [f.absolute()], "new": []}

    if recursive_new:
        d = new.rglob("*")
    else:
        d = new.iterdir()

    for f in d:
        if f.is_file():
            h = GetHash(f)
            if h in hashes:
                hashes[h]["new"].append(f.absolute())

    return RemoveNonDuplicatesON(hashes, nondestructive=False)


def GetONHashesFromHashes(old: dict, new: dict, nondestructive=False):
    """
    Load hashes to form old-new duplicate structure
    """
    if nondestructive:
        old = old.copy()

    for h in old:
        old[h] = {"old": old[h]}

    for h in new:
        if h in old:
            old[h]["new"] = new[h]

    return RemoveNonDuplicatesON(old, nondestructive=False)


def LoadHashes(path, t="str", sep=":"):
    """
    Load hashes from file into standard form
    {hash1: [file1, file2, ...], hash2: [file1, file2, ...]}
    """

    # {hash: [file1, file2, ...]}
    hashes = dict()
    if t == "str":
        # file hash
        with open(path, "r") as f:
            for line in f.read().splitlines():
                tmp = line.split(sep)
                if len(tmp) != 2:
                    continue
                filepath, h = tmp
                filepath = Path(filepath)
                if h in hashes:
                    hashes[h].append(filepath)
                else:
                    hashes[h] = [filepath]
    return hashes


def PickDuplicates(hashes: dict, which="new", nondestructive=False):
    """
    Gets paths to old duplicate files and hash
    which should be equal to 'old' or 'new'
    """
    assert type(hashes) is dict

    if nondestructive:
        hashes = hashes.copy()

    for h in hashes:
        hashes[h] = hashes[h][which]

    return hashes


def PathsFromHashes(hashes, nondestructive=False):
    """
    Get path:hash from hashes
    """
    assert type(hashes) is dict

    paths = {}

    for h in hashes.keys():
        for p in hashes[h]:
            paths[p] = h
        # Saves memory by deleting the values
        # Otherwise uses more than twice the memory at peak
        if not nondestructive:
            hashes.pop(h)
    return paths


def ONToHashes(hashes: dict, nondestructive=False):
    """
    Translates duplicates to standard hashes
    """
    if nondestructive:
        hashes = hashes.copy()

    for h in hashes:
        hashes[h] = hashes[h]["old"] + hashes[h]["new"]

    return hashes


def DumpHashes(hashes: dict, out, sep=":", add=False, overwrite=True):
    """
    Write hashes from standard form into path:hash file
    """
    if overwrite:
        f = open(out, "w")
        f.write("")
        f.close()

    if overwrite and Path(out).exists() and not add:
        return 1

    f = open(out, "a")

    if type(hashes[list(hashes.keys())[0]]) is dict:
        hashes = ONToHashes(hashes)

    for h in hashes:
        for path in hashes[h]:
            f.write(f"{str(path.absolute())}{sep}{str(h)}\n")

    f.close()
    return 0


def SelectDuplicates(hashes: dict, shortest=True, nondestructive=False):
    """
    Return everything but the first occurance of a file with hash
    shortest = True -> sorts the list of paths to keep the shortest path
    """
    if type(hashes[list(hashes.keys())[0]]) is dict:
        hashes = ONToHashes(hashes)

    if nondestructive:
        hashes = hashes.copy()
    for h in list(hashes.keys()):
        if len(hashes[h]) <= 1:
            hashes.pop(h)
            continue
        if shortest:
            hashes[h].sort()
        hashes[h] = hashes[h][1:]

    return hashes


def VerifyHashes(hashes: dict, nondestructive=False):
    """
    Delete paths of files that do not exist and delete hashes if they are empty
    """
    if nondestructive:
        hashes = hashes.copy()

    for h in list(hashes.keys()):
        i = 0
        while i < len(hashes[h]):
            path = hashes[h][i]
            if not path.exists():
                hashes[h].pop(i)
                continue
            i += 1

        if len(hashes[h]) == 0:
            hashes.pop(h)

    return hashes


def PrintHashes(hashes: dict):
    for h in hashes:
        print(f"{h}:", *hashes[h], end="\n\n")
    return 0


def PrintPaths(paths: dict):
    for p in paths:
        print(f"{str(p)}:", paths[p], end="\n\n")
