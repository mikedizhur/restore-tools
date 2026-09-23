from pathlib import Path
from pygments.lexers import guess_lexer


def AnalyzeFile(path: Path, buff=10000) -> str:
    f = open(path, "rb")
    # Read N characters
    text = f.read(buff)
    f.close()

    guess = guess_lexer(text).filenames
    return guess[0].split(".")[-1].lower().strip() if len(guess) >= 1 else None


def GetFileType(
    path: Path, extended=True, buff=10000, analyze_all=False, other=True
) -> str:
    assert path.exists()

    if analyze_all:
        return AnalyzeFile(path, buff)

    name = str(path.name).split(".")

    ext = None

    if len(name) > 1:
        ext = name[-1].lower().strip()
        if not ext.isdigit() and ext != "txt":
            return ext

    if not extended:
        if other and ext is None:
            return "other"
        return ext

    result = AnalyzeFile(path, buff)
    if other and result is None:
        return "other"
    return result
