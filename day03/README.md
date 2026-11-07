# Day 03 – Organic molecular formula calculator

## The task
Find a science computation, write a program with a function that does it, store some data for it in files, and describe what I did and the prompts I used.

## What I chose: the molecular formula of an organic compound
When you make a new compound in an organic chemistry lab, you characterize it with mass spectrometry and elemental analysis. Both start from the molecular formula. From the formula you calculate:

| Quantity | What it is | Used for |
|---|---|---|
| **Molecular weight** (g/mol) | Sum of average atomic masses | Weighing reagents, yields |
| **Monoisotopic (exact) mass** | Sum of the masses of the most abundant isotopes (¹²C, ¹H, ¹⁴N, ¹⁶O …) | High-resolution mass spectrometry |
| **[M+H]⁺** | Exact mass + mass of a proton | The peak seen in ESI-MS |
| **Degree of unsaturation (DBE)** | Rings + π bonds = 1 + Σ nᵢ(vᵢ − 2)/2. For C, H, N, O, X this is (2C + 2 + N − H − X)/2 | Checking a proposed structure. A negative or fractional DBE means the formula can't be a neutral molecule |
| **Elemental composition** (%C, %H, %N) | Mass percent of each element | Comparing with CHN elemental analysis |

## Files
- [`organic_formula.py`](organic_formula.py): the program. Its main functions:
  - `parse_formula(formula)` turns a string like `CH3(CH2)4CH3` or `(C6H5)3P` into atom counts. It handles parentheses and repeated elements.
  - `molecular_weight`, `monoisotopic_mass`, `degree_of_unsaturation`, `percent_composition` do the individual calculations.
  - `analyze(formula)` runs all the calculations for one formula.
  - `analyze_file()` analyzes every compound in `compounds.csv` and writes `results.csv`.
- [`elements.csv`](elements.csv): data for 12 elements common in organic chemistry (H, B, C, N, O, F, Si, P, S, Cl, Br, I): average atomic mass (IUPAC), monoisotopic mass and valence.
- [`compounds.csv`](compounds.csv): 26 organic compounds, from methane to drugs (aspirin, caffeine, ibuprofen), a steroid (cholesterol), and compounds close to my research: perylene, the perylene dye PTCDA (the parent of the perylene diimides we work with in the Rybtchinski lab), and C₆₀.
- [`results.csv`](results.csv): the output of the program for all compounds.
- [`test_organic_formula.py`](test_organic_formula.py): 12 unit tests. They check the results against literature values, e.g. caffeine MW 194.19 and exact mass 194.0804, and aspirin MW 180.16. They also check that invalid formulas raise errors.

## How to run
```bash
cd day03
python3 organic_formula.py                  # analyze compounds.csv → results.csv
python3 organic_formula.py C8H10N4O2 C6H6   # analyze any formulas
python3 -m unittest -v                      # run the tests
```
It needs only the Python standard library (tested with Python 3.9).

Example output:
```
name                           formula             MW  exact mass      [M+H]+  DBE      %C     %H     %N
--------------------------------------------------------------------------------------------------------
benzene                        C6H6             78.11     78.0470     79.0542    4   92.26   7.74   0.00
caffeine                       C8H10N4O2       194.19    194.0804    195.0877    6   49.48   5.19  28.85
PTCDA (perylene dianhydride)   C24H8O6         392.32    392.0321    393.0394   21   73.48   2.06   0.00
buckminsterfullerene           C60             720.66    720.0000    721.0073   61  100.00   0.00   0.00
```

One thing I learned from the tests: I first wrote DBE = 19 for PTCDA in the test, and the test failed. The program was right: (2·24 + 2 − 8)/2 = 21. That is 15 for the perylene core, plus 4 C=O bonds, plus 2 anhydride rings.

## Prompts to AI
I used an AI assistant to write the code. My prompts were:

1. *"Search for some science computation and write a program that has a function that can do this computation. Find or generate data for it and store it in a file. Please do it for something in organic chemistry."*
2. Design choices the AI made from that prompt, which I reviewed:
   - A formula parser that understands parentheses, so condensed formulas like `CH3(CH2)4CH3` and `(C6H5)3P` work.
   - Element data (masses, valences) in a CSV file instead of hard-coded values.
   - Compounds related to my research (perylene, PTCDA).
   - Unit tests that compare the results with literature values.
   - Results saved to `results.csv`.
   - This README.
