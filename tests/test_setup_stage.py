from __future__ import annotations

import unittest

from lcmodel.pipeline.setup import prepare_fit_inputs


class TestSetupStage(unittest.TestCase):
    def test_ppm_window_selection(self):
        matrix = [
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [2.0, 0.0],
        ]
        vector = [10.0, 20.0, 30.0, 40.0]
        ppm = [4.0, 3.0, 2.0, 1.0]
        setup = prepare_fit_inputs(matrix, vector, ppm_axis=ppm, ppm_start=3.1, ppm_end=1.5)
        self.assertEqual((1, 2), setup.row_indices)
        self.assertEqual((20.0, 30.0), setup.vector)

    def test_metabolite_selection(self):
        matrix = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
        ]
        vector = [1.0, 2.0]
        names = ["NAA", "Cr", "Cho"]
        setup = prepare_fit_inputs(
            matrix,
            vector,
            basis_names=names,
            include_metabolites=("Cr", "Cho"),
        )
        self.assertEqual((1, 2), setup.column_indices)
        self.assertEqual(("Cr", "Cho"), setup.metabolite_names)
        self.assertEqual((2.0, 3.0), setup.matrix[0])

    def test_ppm_gap_exclusion(self):
        matrix = [
            [1.0],
            [2.0],
            [3.0],
            [4.0],
        ]
        vector = [10.0, 20.0, 30.0, 40.0]
        ppm = [4.0, 3.0, 2.0, 1.0]
        setup = prepare_fit_inputs(
            matrix,
            vector,
            ppm_axis=ppm,
            ppm_start=4.1,
            ppm_end=0.9,
            exclude_ppm_ranges=((3.2, 2.8),),
        )
        self.assertEqual((0, 2, 3), setup.row_indices)
        self.assertEqual((10.0, 30.0, 40.0), setup.vector)


if __name__ == "__main__":
    unittest.main()
