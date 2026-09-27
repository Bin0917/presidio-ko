import re
from pathlib import Path

README = Path(__file__).parent.parent / "README.md"


def test_readme_example_prints_documented_output(capsys):
    readme = README.read_text(encoding="utf-8")
    code = re.search(r"```python\n(.*?)```", readme, re.S).group(1)
    documented = re.search(r"출력:\n\n```\n(.*?)```", readme, re.S).group(1)

    exec(code, {})

    assert capsys.readouterr().out == documented
