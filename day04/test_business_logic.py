"""More tests for the business logic in organic_formula.py (day 5 assignment).

test_organic_formula.py (from day03) checks the basic calculations.
These tests cover what it did not: the data files, writing results.csv,
the command-line output, harder formulas, exact error messages, and
relations that must hold between the results (chemistry "sanity checks").
"""

import contextlib
import csv
import io
import os
import tempfile
import unittest

import organic_formula
from organic_formula import (
    ELEMENTS,
    PROTON_MASS,
    analyze,
    analyze_file,
    degree_of_unsaturation,
    hill_formula,
    load_compounds,
    load_elements,
    main,
    molecular_weight,
    monoisotopic_mass,
    parse_formula,
    percent_composition,
)


class TestElementData(unittest.TestCase):
    def test_all_twelve_elements_loaded(self):
        self.assertEqual(
            set(ELEMENTS),
            {"H", "B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Br", "I"},
        )

    def test_carbon_12_is_exactly_12(self):
        # The atomic mass unit is defined by carbon-12.
        self.assertEqual(ELEMENTS["C"]["monoisotopic_mass"], 12.0)

    def test_valences(self):
        expected = {"H": 1, "C": 4, "N": 3, "O": 2, "Cl": 1, "Br": 1}
        for symbol, valence in expected.items():
            self.assertEqual(ELEMENTS[symbol]["valence"], valence, symbol)

    def test_masses_are_positive_and_close(self):
        # Average and monoisotopic masses differ by less than 1 u for these elements.
        for symbol, data in ELEMENTS.items():
            self.assertGreater(data["average_mass"], 0, symbol)
            self.assertLess(abs(data["average_mass"] - data["monoisotopic_mass"]), 1, symbol)

    def test_load_elements_from_other_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "elements.csv")
            with open(path, "w", newline="") as fh:
                fh.write("symbol,name,average_mass,monoisotopic_mass,valence\n")
                fh.write("C,carbon,12.011,12.0,4\n")
            self.assertEqual(
                load_elements(path),
                {"C": {"name": "carbon", "average_mass": 12.011,
                       "monoisotopic_mass": 12.0, "valence": 4}},
            )


class TestParseFormulaMore(unittest.TestCase):
    def test_nested_parentheses(self):
        self.assertEqual(parse_formula("C((CH3)3)2"), {"C": 7, "H": 18})

    def test_spaces_are_ignored(self):
        self.assertEqual(parse_formula("C6 H5 OH"), {"C": 6, "H": 6, "O": 1})

    def test_multi_digit_counts(self):
        self.assertEqual(parse_formula("C27H46O"), {"C": 27, "H": 46, "O": 1})

    def test_element_without_number_counts_once(self):
        self.assertEqual(parse_formula("CHBrClF"), {"C": 1, "H": 1, "Br": 1, "Cl": 1, "F": 1})

    def test_different_ways_to_write_the_same_molecule(self):
        # Ethanol written three ways
        for f in ["C2H6O", "CH3CH2OH", "C2H5OH"]:
            self.assertEqual(parse_formula(f), {"C": 2, "H": 6, "O": 1}, f)

    def test_error_messages(self):
        cases = {
            "Xx2": "Unknown element 'Xx'",
            "C6H6)": "Unbalanced ')'",
            "(C6H6": "Unbalanced '('",
            "(2CH3)": "Number directly after '('",
            "2H2O": "Unexpected number",
            "": "Invalid formula",
            "C6H6!": "Invalid formula",
        }
        for formula, message in cases.items():
            with self.assertRaises(ValueError, msg=formula) as ctx:
                parse_formula(formula)
            self.assertIn(message, str(ctx.exception), formula)


class TestHillFormula(unittest.TestCase):
    def test_without_carbon_is_alphabetical(self):
        self.assertEqual(hill_formula(parse_formula("H2O")), "H2O")
        self.assertEqual(hill_formula(parse_formula("NH3")), "H3N")

    def test_carbon_without_hydrogen(self):
        self.assertEqual(hill_formula(parse_formula("CCl4")), "CCl4")
        self.assertEqual(hill_formula(parse_formula("C60")), "C60")

    def test_count_of_one_is_not_written(self):
        self.assertEqual(hill_formula(parse_formula("CH3Br")), "CH3Br")


class TestChemistryRelations(unittest.TestCase):
    def test_isomers_have_same_masses(self):
        # Ethanol and dimethyl ether are both C2H6O.
        a, b = analyze("CH3CH2OH"), analyze("CH3OCH3")
        self.assertEqual(a, b)

    def test_mass_adds_up(self):
        # Adding CH2 to a molecule adds the mass of one C and two H.
        ch2 = molecular_weight(parse_formula("CH2"))
        diff = molecular_weight(parse_formula("C7H16")) - molecular_weight(parse_formula("C6H14"))
        self.assertAlmostEqual(diff, ch2)

    def test_m_plus_h_is_exact_mass_plus_proton(self):
        for f in ["C6H6", "C9H8O4", "C27H46O"]:
            r = analyze(f)
            self.assertAlmostEqual(r["m_plus_h"] - r["monoisotopic_mass"], PROTON_MASS, places=3)

    def test_ring_or_double_bond_removes_two_hydrogens(self):
        # Each extra ring / pi bond means 2 fewer hydrogens and DBE + 1.
        for h, dbe in [(14, 0), (12, 1), (10, 2), (8, 3), (6, 4)]:
            self.assertEqual(degree_of_unsaturation(parse_formula(f"C6H{h}")), dbe)

    def test_halogen_counts_like_hydrogen(self):
        self.assertEqual(
            degree_of_unsaturation(parse_formula("C6H5Cl")),
            degree_of_unsaturation(parse_formula("C6H6")),
        )

    def test_odd_nitrogen_needs_odd_hydrogen(self):
        # Nitrogen rule: C5H5N is fine, C5H4N (half DBE) is not a neutral molecule.
        self.assertEqual(degree_of_unsaturation(parse_formula("C5H5N")), 4)
        with self.assertRaises(ValueError) as ctx:
            degree_of_unsaturation(parse_formula("C5H4N"))
        self.assertIn("DBE = 4.5", str(ctx.exception))

    def test_percent_composition_of_water(self):
        comp = percent_composition(parse_formula("H2O"))
        self.assertAlmostEqual(comp["H"], 11.19, places=2)
        self.assertAlmostEqual(comp["O"], 88.81, places=2)

    def test_percent_nitrogen(self):
        r = analyze("C8H10N4O2")  # caffeine
        self.assertAlmostEqual(r["percent_N"], 28.85, places=2)
        self.assertAlmostEqual(r["percent_C"] + r["percent_H"] + r["percent_N"], 83.52, places=1)

    def test_compound_without_nitrogen_has_zero_percent_n(self):
        self.assertEqual(analyze("C6H6")["percent_N"], 0.0)

    def test_exact_mass_differs_from_average(self):
        # For bromine the two masses differ a lot (79Br vs 79.904 average).
        atoms = parse_formula("CH3Br")
        self.assertGreater(molecular_weight(atoms) - monoisotopic_mass(atoms), 0.9)


class TestCompoundFiles(unittest.TestCase):
    def test_every_stored_compound_is_valid(self):
        compounds = load_compounds()
        self.assertEqual(len(compounds), 26)
        for c in compounds:
            with self.subTest(c["name"]):
                analyze(c["formula"])  # must not raise

    def test_results_csv_is_up_to_date(self):
        # results.csv in the folder must match what the program calculates now.
        with open(organic_formula.RESULTS_FILE, newline="") as fh:
            saved = list(csv.DictReader(fh))
        self.assertEqual(len(saved), 26)
        for row in saved:
            with self.subTest(row["name"]):
                fresh = analyze(row["formula"])
                self.assertEqual(int(row["dbe"]), fresh["dbe"])
                self.assertAlmostEqual(float(row["molecular_weight"]), fresh["molecular_weight"])

    def test_analyze_file_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(src, "w", newline="") as fh:
                fh.write("name,formula,class\nbenzene,C6H6,arene\nwater,H2O,inorganic\n")
            rows = analyze_file(src, out)
            with open(out, newline="") as fh:
                written = list(csv.DictReader(fh))
        self.assertEqual([r["name"] for r in rows], ["benzene", "water"])
        self.assertEqual(written[0]["formula"], "C6H6")
        self.assertEqual(written[0]["dbe"], "4")
        self.assertEqual(written[1]["class"], "inorganic")
        self.assertEqual(list(written[0])[:3], ["name", "class", "formula"])

    def test_analyze_file_stops_on_bad_formula(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "in.csv")
            with open(src, "w", newline="") as fh:
                fh.write("name,formula,class\nbad,Xy3,none\n")
            with self.assertRaises(ValueError):
                analyze_file(src, os.path.join(tmp, "out.csv"))


class TestCommandLine(unittest.TestCase):
    def run_main(self, args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(args)
        return buf.getvalue()

    def test_formulas_from_command_line(self):
        out = self.run_main(["C8H10N4O2", "C6H6"])
        lines = out.splitlines()
        self.assertIn("exact mass", lines[0])
        self.assertEqual(len(lines), 4)  # header, separator line, 2 results
        self.assertIn("194.19", lines[2])
        self.assertIn("78.11", lines[3])

    def test_condensed_formula_printed_in_hill_order(self):
        out = self.run_main(["CH3(CH2)4CH3"])
        self.assertIn("C6H14", out)


if __name__ == "__main__":
    unittest.main()
