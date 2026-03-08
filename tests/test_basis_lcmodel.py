from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from lcmodel.io.basis import is_lcmodel_basis_file, load_lcmodel_basis


class TestLcmodelBasisLoader(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_load_lcmodel_basis(self):
        p = self._make_local_tmpdir()
        try:
            basis = p / "mini.basis"
            basis.write_text(
                (
                    "$BASIS1\n"
                    " NDATAB=4 $END\n"
                    "$NMUSED\n"
                    " FILERAW='Met1' $END\n"
                    "$BASIS\n"
                    " METABO='Met1' $END\n"
                    " 1 0  2 0  3 0  4 0\n"
                    "$NMUSED\n"
                    " FILERAW='Met2' $END\n"
                    "$BASIS\n"
                    " METABO='Met2' $END\n"
                    " 10 0  20 0  30 0  40 0\n"
                ),
                encoding="utf-8",
            )
            self.assertTrue(is_lcmodel_basis_file(basis))
            loaded = load_lcmodel_basis(basis)
            self.assertEqual(4, loaded.ndata)
            self.assertEqual(("Met1", "Met2"), loaded.metabolite_names)
            self.assertEqual(4, len(loaded.matrix_time_domain))
            self.assertEqual(2, len(loaded.matrix_time_domain[0]))
            self.assertEqual(complex(1.0, 0.0), loaded.matrix_time_domain[0][0])
            self.assertEqual(complex(10.0, 0.0), loaded.matrix_time_domain[0][1])
            self.assertEqual(complex(4.0, 0.0), loaded.matrix_time_domain[3][0])
            self.assertEqual(complex(40.0, 0.0), loaded.matrix_time_domain[3][1])
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
