import re
from pathlib import Path

README = Path(__file__).parent.parent / "README.md"


def test_readme_example_prints_documented_output(capsys):
    readme = README.read_text(encoding="utf-8")
    code = re.search(r"```python\n(.*?)```", readme, re.S).group(1)
    documented = re.search(r"출력:\n\n```\n(.*?)```", readme, re.S).group(1)

    exec(code, {})

    assert capsys.readouterr().out == documented


def test_text_files_have_no_control_characters():
    root = README.parent
    paths = [
        README,
        root / "AGENTS.md",
        *root.glob("src/**/*.py"),
        *root.glob("tests/**/*.py"),
    ]
    found = [
        (path.name, line)
        for path in paths
        for line, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text)
    ]
    assert found == []
