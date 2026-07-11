"""TextFSM template loader and parser helper."""

from pathlib import Path

import textfsm

TEMPLATE_DIR = Path(__file__).parent / "templates"


def parse_with_textfsm(template_name: str, cli_output: str) -> list[dict[str, str]]:
    """Parse CLI output using a named TextFSM template in templates/."""
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"TextFSM template not found: {template_path}")

    with template_path.open(encoding="utf-8") as handle:
        fsm = textfsm.TextFSM(handle)

    rows = fsm.ParseText(cli_output)
    return [dict(zip(fsm.header, row)) for row in rows]
