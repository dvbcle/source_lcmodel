from __future__ import annotations

import re
import unittest
from pathlib import Path


_HEADER_RE = re.compile(
    r"^\s*(?:(REAL|INTEGER|LOGICAL|COMPLEX|DOUBLE\s+PRECISION|CHARACTER(?:\*\d+)?)\s+)?"
    r"(PROGRAM|SUBROUTINE|FUNCTION|BLOCK\s+DATA)(?:\s+([A-Za-z_][\w$]*))?",
    flags=re.IGNORECASE,
)
_DEF_RE = re.compile(r"\bdef\s+([a-zA-Z_]\w*)\s*\(", flags=re.IGNORECASE)


def _sanitize(name: str) -> str:
    out = re.sub(r"[^0-9a-zA-Z_]", "_", name.strip()).lower()
    if not out:
        out = "unnamed"
    if out[0].isdigit():
        out = f"n_{out}"
    return out


class TestFortranScaffoldCoverage(unittest.TestCase):
    def test_named_program_units_have_python_scaffold_functions(self):
        fortran_source = Path("LCModel.f").read_text(encoding="utf-8", errors="replace")
        required: set[str] = set()
        for line in fortran_source.splitlines():
            m = _HEADER_RE.match(line)
            if not m:
                continue
            raw_name = (m.group(3) or "").strip()
            if not raw_name:
                continue
            required.add(_sanitize(raw_name))

        scaffold_source = Path("lcmodel/fortran_scaffold.py").read_text(
            encoding="utf-8", errors="replace"
        )
        available = {m.group(1) for m in _DEF_RE.finditer(scaffold_source)}

        missing = sorted(required - available)
        self.assertFalse(
            missing,
            f"Missing scaffold functions for Fortran program units: {', '.join(missing)}",
        )


if __name__ == "__main__":
    unittest.main()
