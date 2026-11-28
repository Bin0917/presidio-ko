import ast
import io
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCES = sorted([*ROOT.glob("src/**/*.py"), *ROOT.glob("tests/**/*.py")])
DOCUMENTED = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_source_has_no_comments_or_docstrings(path):
    source = path.read_text(encoding="utf-8")
    comments = [
        token.start[0]
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    ]
    docstrings = [
        node.body[0].lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, DOCUMENTED) and ast.get_docstring(node) is not None
    ]
    assert (comments, docstrings) == ([], [])
