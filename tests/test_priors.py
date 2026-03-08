from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from lcmodel.engine import LCModelRunner
from lcmodel.io.priors import load_soft_priors
from lcmodel.models import RunConfig
from lcmodel.pipeline.priors import augment_system_with_soft_priors


class TestPriors(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_load_soft_priors(self):
        p = self._make_local_tmpdir()
        try:
            f = p / "priors.txt"
            f.write_text("NAA 1.0 0.2\nCr 2.0 0.5\n", encoding="utf-8")
            priors = load_soft_priors(f)
            self.assertEqual((1.0, 0.2), priors["naa"])
            self.assertEqual((2.0, 0.5), priors["cr"])
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_augment_system_with_soft_priors(self):
        mat, vec = augment_system_with_soft_priors(
            [[1.0, 0.0], [0.0, 1.0]],
            [1.0, 2.0],
            ["NAA", "Cr"],
            {"cr": (3.0, 0.1)},
        )
        self.assertEqual(3, len(mat))
        self.assertEqual(3, len(vec))
        self.assertAlmostEqual(10.0, mat[-1][1], places=6)
        self.assertAlmostEqual(30.0, vec[-1], places=6)

    def test_engine_uses_priors(self):
        p = self._make_local_tmpdir()
        try:
            vec = p / "vec.txt"
            mat = p / "mat.txt"
            names = p / "names.txt"
            priors = p / "priors.txt"
            vec.write_text("1\n1\n", encoding="utf-8")
            mat.write_text("1 0\n1 0\n", encoding="utf-8")
            names.write_text("NAA\nCr\n", encoding="utf-8")
            priors.write_text("Cr 2.0 0.1\n", encoding="utf-8")

            result = LCModelRunner(
                RunConfig(
                    raw_data_file=str(vec),
                    basis_file=str(mat),
                    basis_names_file=str(names),
                    priors_file=str(priors),
                )
            ).run()
            self.assertIsNotNone(result.fit_result)
            assert result.fit_result is not None
            # Cr receives value from prior even though it is absent from raw system.
            self.assertGreater(result.fit_result.coefficients[1], 1.5)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

