# Day 04 – A web interface for the organic formula calculator

## The task
Take a previous assignment, copy it to `day04` so the old one stays intact, and write a web application (e.g. with Flask) that uses the "business logic" of the previous program. Check that both the old and the new systems work.

## What I did
**Live demo: https://organic-formula.onrender.com/**

I copied my [day03](../day03) organic molecular formula calculator into this folder without changing it. All the chemistry is still in [`organic_formula.py`](organic_formula.py). The new file [`app.py`](app.py) is a small Flask application that imports this module and puts web pages around it. It does no calculations itself.

The web app has three pages:

| URL | What it shows |
|---|---|
| `/` | A form. Type a formula (e.g. `C8H10N4O2` or `CH3(CH2)4CH3`) and get the molecular weight, exact mass, [M+H]⁺, degree of unsaturation and the elemental composition of every element. Invalid formulas show the error message from the program, e.g. *"Formula C6H7 is not a valid neutral molecule (DBE = 3.5)"*. |
| `/compounds` | A table of all 26 compounds in `compounds.csv` with their results. Clicking a formula opens it in the calculator. |
| `/api/<formula>` | The same results as JSON, e.g. `/api/C9H8O4` for aspirin. Invalid formulas return status 400 with an `error` field. |

## Files
- [`app.py`](app.py): the Flask web application (new).
- [`templates/`](templates): the HTML pages (new). `base.html` has the layout shared by the other two pages.
- [`test_app.py`](test_app.py): 7 tests for the web app using Flask's test client (new). They check the form, a formula given in the URL, an invalid formula, the compound list and the JSON API.
- [`requirements.txt`](requirements.txt): Flask, and gunicorn for the deployment (new).
- `organic_formula.py`, `elements.csv`, `compounds.csv`, `results.csv`, `test_organic_formula.py`: copied from day03, unchanged.

## How to run
```bash
cd day04
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 app.py               # web app: open http://127.0.0.1:5001
python3 organic_formula.py   # the old command-line program still works
python3 -m unittest -v       # all 19 tests (12 old + 7 new)
```

The app runs on port 5001 and not Flask's default 5000, because on macOS port 5000 is taken by the AirPlay Receiver. When I first ran it on 5000 every page returned *403 Forbidden*, and that was not Flask answering.

## Deployment (beyond the requirements)
The app is live at **https://organic-formula.onrender.com/**, deployed on [Render](https://render.com) (free plan).

- [`render.yaml`](../render.yaml) in the repository root is a Render "Blueprint". It tells Render to use the `day04` folder, install `requirements.txt`, and start the app with `gunicorn --bind 0.0.0.0:$PORT app:app`.
- [gunicorn](https://gunicorn.org/) is a production web server. `python3 app.py` uses Flask's development server, which is fine on my laptop but not meant for the internet.
- Every push to `main` redeploys the app automatically.
- On the free plan the app sleeps after about 15 minutes without visitors, so the first page load after that takes about 30 seconds.

To set it up I signed in to Render with my GitHub account, chose **New → Blueprint**, and picked this repository.

## Checking that both systems work
- **Old system (day03):** `python3 -m unittest` in `day03` passes all 12 tests, and `python3 organic_formula.py C8H10N4O2` prints caffeine's results (MW 194.19, exact mass 194.0804).
- **New system (day04):** all 19 tests pass. I also started the server and opened the pages: `/api/C9H8O4` returned MW 180.16 for aspirin, `/compounds` loaded, the calculator showed 392.32 g/mol for PTCDA (C₂₄H₈O₆), and `/api/C6H7` returned a 400 error because its DBE is 3.5.

One test failed the first time: I expected the error for `Xx2` to say "Invalid formula", but the program says *"Unknown element 'Xx' in 'Xx2'"*, which is more useful. The test was wrong, not the program.

## Prompts to AI
I used an AI assistant (Claude Code) to write the code. My prompt was the assignment text:

1. *"Take the previous assignment … copy it to the day04 folder … write a web application (e.g. using Flask) that will use the 'business logic' from the previous implementation and provide a web interface to it. Check that both the old and the new systems work."*

Design choices the AI made, which I reviewed:
- Keep `organic_formula.py` unchanged and import it, so the CLI and the web app use exactly the same code.
- Three pages: a calculator form, a list of the stored compounds, and a JSON API.
- Show the program's own error messages for bad input on the page instead of crashing.
- Tests with Flask's test client, so no running server is needed for testing.
