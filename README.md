# RoleReady
Placement & internship **readiness** platform. Naukri/LinkedIn tell you where to apply; RoleReady tells you whether you can be ready in time, and what to learn first. **Stack:** Flask (Python) - MySQL (main DB) - MongoDB (resume analyses, optional) - Jinja2/HTML/CSS.

## Modules implemented
| # | Module | Where |
|---|--------|-------|
| 1 | Student profile & preferences | `/profile` |
| 2 | Opportunity discovery (search, filter, sort) | `/opportunities` |
| 3 | Eligibility & matching (transparent rules) | `/matches`, `matching.py` |
| 4 | Resume analysis (PDF/DOCX/TXT) | `/resume`, `resume.py` |
| 5 | Skill-gap analysis | `/gap` |
| 8 | Application & deadline tracking | `/tracker` |

| 6 | Readiness-to-deadline, evidence-weighted skills, "learn first", skill tests | `/readiness`, `/tests`, `readiness.py`, `tests_data.py` |
| 7 | Personalised weekly plan | `/plan` |
| - | Editable estimated hours per skill | `/hours` |

### The core idea (Modules 6-7)
*Given what a student can actually prove today, and the days left before each deadline, which opportunities can they realistically be ready for, and what is the shortest preparation path?*
- **Evidence weights** (our own design choice): self-declared 0.5, found in resume 0.75, passed skill test (>=60%) 1.0.
- **Hours still needed** = estimated hours x (1 - evidence weight). **Hours available** = weekly study hours x days left / 7.
- **Labels:** Ready (<=2 h needed), Reachable (needed <= available), Stretch (<= 1.5x available), Not feasible.
- **Learn first:** each missing/unproven skill is simulated as proven; skills are ranked by how many opportunities move to a better label, then by coverage gain.
- **Weekly plan:** skills ordered by earliest deadline served, then by number of opportunities served, poured into weeks of the student's study hours.
- **Skill tests:** 8 skills x 10 questions plus 3 mock-interview questions each; every attempt is stored in MongoDB (SQL table if Mongo is not configured).

Run the tests with `python test_readiness.py` (or `pytest`).

## Quick start (no database needed)
    pip install -r requirements.txt
    python app.py            # uses SQLite automatically -> http://127.0.0.1:5000

## With MySQL (+ optional MongoDB)
    mysql -u root -p -e "CREATE DATABASE roleready CHARACTER SET utf8mb4;"
    cp .env.example .env     # edit passwords; DB_BACKEND=mysql
    pip install python-dotenv
    python app.py            # creates tables + sample data on first run

Set `MONGO_URI` to store resume analyses as MongoDB documents; leave blank to use a MySQL table.

## Database design (MySQL)
students 1--* applications *--1 opportunities; students 1--* resume_analyses (or a Mongo collection of the same name).

## 5-minute demo script
1. Module 1 - "+ New", create a profile (skills: python, sql, flask), show it saved; edit it.
2. Module 2 - search "python", filter Internship + Pune; point out Eligible / Not eligible and deadlines.
3. Module 3 - My Matches: open "How is the score calculated?" and a score breakdown (hard eligibility, then 60/15/15/10 scoring).
4. Module 4 - upload a resume; show score, skills, feedback, "Add them to my profile"; return to Matches and show scores rise.
5. Module 5 - Skill Gap: pick "Backend Developer Intern"; show gaps, evidence (profile/resume) and tips.
6. Modules 6-7 - open Readiness: show the Ready/Reachable/Stretch labels and "Learn these first"; take the SQL test, return and show the label/hours change; open Plan.
7. Module 8 - save two opportunities, move one to Applied/Interview, show the deadline reminder.
Demo students (Aarav, Diya) are in the top-right dropdown.

## Limitations (mention before they ask)
- No password login yet (profile-selection session); planned: Flask-Login + hashed passwords.
- Opportunity data is sample data; admin upload / scraping is future work.
- Hours per skill are estimates (editable); weights and thresholds are design choices, not validated against placement outcomes yet.
- 'Reachable' is a planning aid, not a prediction of being shortlisted or selected.
- Not yet built: placement-cell/admin side, CSV drive upload, backlog and 10th/12th eligibility fields, outcome tracking, e-mail reminders.
- Resume parsing is rule-based (skill dictionary + checklist), not ML; scanned PDFs unsupported.
