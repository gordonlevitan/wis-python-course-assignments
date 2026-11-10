"""Organic molecular formula calculator.

Given a molecular formula such as ``C9H8O4`` (aspirin) or ``CH3(CH2)4CH3``
(hexane), compute the numbers an organic chemist usually needs:

* molecular weight (average atomic masses, g/mol)
* monoisotopic (exact) mass and the [M+H]+ ion, as seen in mass spectrometry
* degree of unsaturation (DBE = rings + pi bonds)
* elemental composition (mass %), as reported in elemental analysis (CHN)

Element data is read from ``elements.csv`` and a list of example compounds
from ``compounds.csv``, both in the same folder as this file.

Usage:
    python3 organic_formula.py                 # analyze all compounds in compounds.csv
    python3 organic_formula.py C8H10N4O2 C6H6  # analyze formulas given on the command line
"""

import csv
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ELEMENTS_FILE = os.path.join(HERE, "elements.csv")
COMPOUNDS_FILE = os.path.join(HERE, "compounds.csv")
RESULTS_FILE = os.path.join(HERE, "results.csv")

PROTON_MASS = 1.007276466  # mass of H+ (u), used for the [M+H]+ ion

TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+)")


def load_elements(path=ELEMENTS_FILE):
    """Read element data from a CSV file into a dict keyed by element symbol."""
    elements = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            elements[row["symbol"]] = {
                "name": row["name"],
                "average_mass": float(row["average_mass"]),
                "monoisotopic_mass": float(row["monoisotopic_mass"]),
                "valence": int(row["valence"]),
            }
    return elements


ELEMENTS = load_elements()


def parse_formula(formula):
    """Turn a formula string into a Counter of element -> number of atoms.

    Supports nested parentheses, e.g. ``(C6H5)3P`` or ``CH3(CH2)4CH3``.
    """
    formula = formula.replace(" ", "")
    tokens = TOKEN.findall(formula)
    if "".join(tokens) != formula or not formula:
        raise ValueError("Invalid formula: {!r}".format(formula))

    stack = [Counter()]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        i += 1
        count = 1
        if i < len(tokens) and tokens[i].isdigit():
            count = int(tokens[i])
            i += 1
        if tok == "(":
            if count != 1:
                raise ValueError("Number directly after '(' in {!r}".format(formula))
            stack.append(Counter())
        elif tok == ")":
            if len(stack) == 1:
                raise ValueError("Unbalanced ')' in {!r}".format(formula))
            group = stack.pop()
            for element, n in group.items():
                stack[-1][element] += n * count
        elif tok.isdigit():
            raise ValueError("Unexpected number in {!r}".format(formula))
        else:
            if tok not in ELEMENTS:
                raise ValueError("Unknown element {!r} in {!r}".format(tok, formula))
            stack[-1][tok] += count
    if len(stack) != 1:
        raise ValueError("Unbalanced '(' in {!r}".format(formula))
    return stack[0]


def hill_formula(atoms):
    """Write the formula in Hill order: C, then H, then the rest alphabetically."""
    order = []
    if "C" in atoms:
        order = ["C"] + (["H"] if "H" in atoms else [])
    order += sorted(el for el in atoms if el not in order)
    return "".join(el + (str(atoms[el]) if atoms[el] > 1 else "") for el in order)


def molecular_weight(atoms):
    """Average molecular weight in g/mol."""
    return sum(ELEMENTS[el]["average_mass"] * n for el, n in atoms.items())


def monoisotopic_mass(atoms):
    """Exact mass of the most abundant isotopes (u)."""
    return sum(ELEMENTS[el]["monoisotopic_mass"] * n for el, n in atoms.items())


def degree_of_unsaturation(atoms):
    """Rings plus double bonds: DBE = 1 + sum(n_i * (valence_i - 2)) / 2.

    For C, H, N, O, X this is the familiar (2C + 2 + N - H - X) / 2.
    """
    dbe = 1 + sum(n * (ELEMENTS[el]["valence"] - 2) for el, n in atoms.items()) / 2
    if dbe < 0 or dbe != int(dbe):
        raise ValueError("Formula {} is not a valid neutral molecule (DBE = {})".format(
            hill_formula(atoms), dbe))
    return int(dbe)


def percent_composition(atoms):
    """Mass percent of each element, as in elemental analysis."""
    mw = molecular_weight(atoms)
    return {el: 100 * ELEMENTS[el]["average_mass"] * n / mw for el, n in atoms.items()}


def analyze(formula):
    """Do all the calculations for one formula and return them as a dict."""
    atoms = parse_formula(formula)
    composition = percent_composition(atoms)
    exact = monoisotopic_mass(atoms)
    return {
        "formula": hill_formula(atoms),
        "molecular_weight": round(molecular_weight(atoms), 2),
        "monoisotopic_mass": round(exact, 4),
        "m_plus_h": round(exact + PROTON_MASS, 4),
        "dbe": degree_of_unsaturation(atoms),
        "percent_C": round(composition.get("C", 0.0), 2),
        "percent_H": round(composition.get("H", 0.0), 2),
        "percent_N": round(composition.get("N", 0.0), 2),
    }


def load_compounds(path=COMPOUNDS_FILE):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def analyze_file(path=COMPOUNDS_FILE, out_path=RESULTS_FILE):
    """Analyze every compound in a CSV file and write the results to another CSV."""
    rows = []
    for compound in load_compounds(path):
        result = {"name": compound["name"], "class": compound["class"]}
        result.update(analyze(compound["formula"]))
        rows.append(result)
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def print_table(rows):
    header = "{:<30} {:<12} {:>9} {:>11} {:>11} {:>4} {:>7} {:>6} {:>6}".format(
        "name", "formula", "MW", "exact mass", "[M+H]+", "DBE", "%C", "%H", "%N")
    print(header)
    print("-" * len(header))
    for r in rows:
        print("{:<30} {:<12} {:>9.2f} {:>11.4f} {:>11.4f} {:>4} {:>7.2f} {:>6.2f} {:>6.2f}".format(
            r.get("name", ""), r["formula"], r["molecular_weight"], r["monoisotopic_mass"],
            r["m_plus_h"], r["dbe"], r["percent_C"], r["percent_H"], r["percent_N"]))


def main(argv):
    if argv:
        rows = [analyze(f) for f in argv]
    else:
        rows = analyze_file()
        print("Results written to {}\n".format(os.path.basename(RESULTS_FILE)))
    print_table(rows)


if __name__ == "__main__":
    main(sys.argv[1:])
