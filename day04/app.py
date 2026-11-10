"""Web interface for the organic molecular formula calculator.

The calculations ("business logic") all live in ``organic_formula.py``,
the same module used by the command-line program. This file only adds
web pages around it.

Run:
    python3 app.py           # then open http://127.0.0.1:5001
"""

from flask import Flask, jsonify, render_template, request

import organic_formula

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    """A form where you type a formula and see the results."""
    formula = request.values.get("formula", "").strip()
    result = None
    error = None
    if formula:
        try:
            result = organic_formula.analyze(formula)
            atoms = organic_formula.parse_formula(formula)
            composition = organic_formula.percent_composition(atoms)
            result["composition"] = [
                (el, organic_formula.ELEMENTS[el]["name"], atoms[el], round(pct, 2))
                for el, pct in sorted(composition.items(), key=lambda kv: -kv[1])
            ]
        except ValueError as exc:
            error = str(exc)
    return render_template("index.html", formula=formula, result=result, error=error)


@app.route("/compounds")
def compounds():
    """Table of all the compounds stored in compounds.csv."""
    rows = []
    for compound in organic_formula.load_compounds():
        row = {"name": compound["name"], "class": compound["class"]}
        row.update(organic_formula.analyze(compound["formula"]))
        rows.append(row)
    return render_template("compounds.html", rows=rows)


@app.route("/api/<formula>")
def api(formula):
    """The same calculation as JSON, e.g. /api/C8H10N4O2"""
    try:
        return jsonify(organic_formula.analyze(formula))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    # port 5000 is used by the macOS AirPlay Receiver, so use 5001
    app.run(debug=True, port=5001)
