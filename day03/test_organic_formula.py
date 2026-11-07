import unittest

from organic_formula import (
    analyze,
    degree_of_unsaturation,
    hill_formula,
    molecular_weight,
    monoisotopic_mass,
    parse_formula,
    percent_composition,
)


class TestParseFormula(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_formula("C6H6"), {"C": 6, "H": 6})

    def test_two_letter_elements(self):
        self.assertEqual(parse_formula("CHCl3"), {"C": 1, "H": 1, "Cl": 3})

    def test_parentheses(self):
        self.assertEqual(parse_formula("CH3(CH2)4CH3"), {"C": 6, "H": 14})
        self.assertEqual(parse_formula("(C6H5)3P"), {"C": 18, "H": 15, "P": 1})

    def test_repeated_elements_are_summed(self):
        self.assertEqual(parse_formula("CH3COOH"), {"C": 2, "H": 4, "O": 2})

    def test_invalid(self):
        for bad in ["", "Xx2", "C6H6)", "(C6H6", "c6h6", "C6-H6"]:
            with self.assertRaises(ValueError, msg=bad):
                parse_formula(bad)


class TestCalculations(unittest.TestCase):
    def test_hill_formula(self):
        self.assertEqual(hill_formula(parse_formula("CH3COOH")), "C2H4O2")
        self.assertEqual(hill_formula(parse_formula("OSC2H6")), "C2H6OS")

    def test_molecular_weight(self):
        # literature values (g/mol)
        self.assertAlmostEqual(molecular_weight(parse_formula("C9H8O4")), 180.16, places=2)
        self.assertAlmostEqual(molecular_weight(parse_formula("C8H10N4O2")), 194.19, places=2)
        self.assertAlmostEqual(molecular_weight(parse_formula("C24H8O6")), 392.32, places=2)

    def test_monoisotopic_mass(self):
        self.assertAlmostEqual(monoisotopic_mass(parse_formula("C8H10N4O2")), 194.0804, places=4)
        self.assertAlmostEqual(monoisotopic_mass(parse_formula("C60")), 720.0, places=4)

    def test_degree_of_unsaturation(self):
        cases = {"CH4": 0, "C2H4": 1, "C2H2": 2, "C6H12": 1, "C6H6": 4,
                 "C10H8": 7, "C5H5N": 4, "C6H5Br": 4, "C2H6OS": 0,
                 "C27H46O": 5, "C24H8O6": 21, "C60": 61}
        for formula, dbe in cases.items():
            self.assertEqual(degree_of_unsaturation(parse_formula(formula)), dbe, formula)

    def test_impossible_formula(self):
        with self.assertRaises(ValueError):
            degree_of_unsaturation(parse_formula("CH5"))   # DBE = -0.5
        with self.assertRaises(ValueError):
            degree_of_unsaturation(parse_formula("CH6"))   # DBE = -1

    def test_percent_composition_sums_to_100(self):
        comp = percent_composition(parse_formula("C8H9NO2"))
        self.assertAlmostEqual(sum(comp.values()), 100.0)
        self.assertAlmostEqual(comp["C"], 63.56, places=2)

    def test_analyze(self):
        r = analyze("C8H10N4O2")
        self.assertEqual(r["formula"], "C8H10N4O2")
        self.assertEqual(r["dbe"], 6)
        self.assertAlmostEqual(r["m_plus_h"], 195.0877, places=4)


if __name__ == "__main__":
    unittest.main()
