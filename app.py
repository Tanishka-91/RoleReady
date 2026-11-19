"""RoleReady - placement & internship readiness platform (Review 2 demo).
Run:  python app.py   ->  http://127.0.0.1:5000
"""
import json
import os
from collections import Counter
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

import db
import matching as M
import random
import readiness as RD
import resume as R
import tests_data as TD
from skills_data import DEFAULT_TIP, LEARN_TIPS, SKILL_CATALOG, sample_opportunities

# Load .env if python-dotenv is present (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
app.teardown_appcontext(db.close)

STATUSES = ["Saved", "Applied", "Online Test", "Interview", "Offer", "Rejected"]
BRANCHES = ["Computer Science", "Information Technology", "Electronics", "Data Science", "AI & ML", "Mechanical", "Civil"]
DEGREES = ["B.Tech", "B.E.", "BCA", "B.Sc", "M.Tech", "MCA"]


# ---------------------------------------------------------------- storage helpers
_mongo = {}
SQL_NAME = {"sqlite": "SQLite", "mysql": "MySQL"}.get(db.BACKEND, db.BACKEND)


def mongo_col(name="resume_analyses"):
    """MongoDB collection (resume analyses / skill test attempts), or None when Mongo isn't configured."""
    uri = os.getenv("MONGO_URI")
    if not uri:
        return None
    if name not in _mongo:
        try:
            from pymongo import MongoClient
            client = MongoClient(uri, serverSelectionTimeoutMS=1500)
            client.admin.command("ping")
            _mongo[name] = client[os.getenv("MONGO_DB", "roleready")][name]
        except Exception as e:  # fall back to SQL table
            print("MongoDB unavailable, using SQL table:", e)
            _mongo[name] = False
    return _mongo[name] or None


def save_analysis(student_id, analysis):
    col = mongo_col()
    if col is not None:
        col.insert_one({"student_id": student_id, **analysis})
        return "MongoDB"
    db.execute("INSERT INTO resume_analyses (student_id, data, created_at) VALUES (?,?,?)",
               (student_id, json.dumps(analysis), analysis["created_at"]))
    return SQL_NAME


def latest_analysis(student_id):
    col = mongo_col()
    if col is not None:
        doc = col.find_one({"student_id": student_id}, sort=[("_id", -1)], projection={"_id": 0, "student_id": 0})
        return doc
    row = db.query("SELECT data FROM resume_analyses WHERE student_id=? ORDER BY id DESC LIMIT 1", (student_id,), one=True)
    return json.loads(row["data"]) if row else None


def save_test_attempt(student_id, skill, score, total):
    now = datetime.now().isoformat(timespec="seconds")
    col = mongo_col("skill_tests")
    if col is not None:
        col.insert_one({"student_id": student_id, "skill": skill, "score": score, "total": total, "created_at": now})
        return "MongoDB"
    db.execute("INSERT INTO skill_tests (student_id, skill, score, total, created_at) VALUES (?,?,?,?,?)",
               (student_id, skill, score, total, now))
    return SQL_NAME


def test_attempts(student_id):
    col = mongo_col("skill_tests")
    if col is not None:
        return list(col.find({"student_id": student_id}, projection={"_id": 0}).sort("created_at", -1))
    return db.query("SELECT skill, score, total, created_at FROM skill_tests WHERE student_id=? ORDER BY id DESC", (student_id,))


def tested_best(student_id):
    """{skill: best score in %} over all attempts."""
    best = {}
    for a in test_attempts(student_id):
        pct = 100 * a["score"] / a["total"]
        best[a["skill"]] = max(best.get(a["skill"], 0), pct)
    return best


def skill_hours():
    h = dict(RD.DEFAULT_SKILL_HOURS)
    for r in db.query("SELECT skill, hours FROM skill_hours"):
        h[r["skill"]] = r["hours"]
    return h


# ---------------------------------------------------------------- session helpers
def current_student():
    sid = session.get("student_id")
    return db.query("SELECT * FROM students WHERE id=?", (sid,), one=True) if sid else None


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not current_student():
            flash("Create or select a student profile first.", "warn")
            return redirect(url_for("profile"))
        return f(*a, **kw)
    return wrapper


@app.context_processor
def inject():
    return {"me": current_student(), "all_students": db.query("SELECT id, name FROM students ORDER BY name"),
            "today": date.today().isoformat()}


def days_left(deadline):
    try:
        return (datetime.strptime(deadline, "%Y-%m-%d").date() - date.today()).days
    except (TypeError, ValueError):
        return None


app.jinja_env.globals["days_left"] = days_left
app.jinja_env.filters["csv"] = M.split


def student_skills_with_resume(student):
    a = latest_analysis(student["id"])
    return (set(a["skills"]) if a else set()), a


# ---------------------------------------------------------------- Module 1: profile
@app.route("/profile", methods=["GET", "POST"])
def profile():
    me = current_student()
    if request.method == "POST":
        f = request.form
        skills = ", ".join(sorted({M.norm_skill(s) for s in M.split(f.get("skills"))}))
        vals = (f["name"].strip(), f["email"].strip().lower(), f["degree"], f["branch"],
                int(f["grad_year"]), float(f["cgpa"]), skills, f.get("pref_companies", ""),
                f.get("pref_roles", ""), f.get("pref_locations", ""), max(1, min(80, int(f.get("weekly_hours") or 10))))
        try:
            if me:
                db.execute("""UPDATE students SET name=?, email=?, degree=?, branch=?, grad_year=?, cgpa=?,
                              skills=?, pref_companies=?, pref_roles=?, pref_locations=?, weekly_hours=? WHERE id=?""", vals + (me["id"],))
                flash("Profile updated.", "ok")
            else:
                sid = db.execute("""INSERT INTO students (name,email,degree,branch,grad_year,cgpa,skills,
                                    pref_companies,pref_roles,pref_locations,weekly_hours,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                 vals + (datetime.now().isoformat(timespec="seconds"),))
                session["student_id"] = sid
                flash("Profile created and saved to the database.", "ok")
        except Exception as e:
            flash(f"Could not save profile (is the email already registered?): {e}", "err")
            return redirect(url_for("profile"))
        return redirect(url_for("dashboard"))
    return render_template("profile.html", s=me, branches=BRANCHES, degrees=DEGREES, catalog=SKILL_CATALOG)


@app.route("/switch/<int:sid>")
def switch(sid):
    if db.query("SELECT id FROM students WHERE id=?", (sid,), one=True):
        session["student_id"] = sid
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/new")
def new_profile():
    session.pop("student_id", None)
    return redirect(url_for("profile"))


# ---------------------------------------------------------------- dashboard
@app.route("/")
def home():
    return redirect(url_for("dashboard")) if current_student() else render_template("home.html")


@app.route("/dashboard")
@login_required
def dashboard():
    me = current_student()
    extra, analysis = student_skills_with_resume(me)
    opps = db.query("SELECT * FROM opportunities")
    ranked = M.rank(me, opps, extra)
    eligible = [r for r in ranked if r["eligible"]]
    apps = db.query("""SELECT a.*, o.company, o.role, o.deadline FROM applications a
                       JOIN opportunities o ON o.id=a.opportunity_id WHERE a.student_id=? ORDER BY o.deadline""", (me["id"],))
    upcoming = [a for a in apps if a["status"] in ("Saved",) and (days_left(a["deadline"]) or -1) >= 0][:4]
    counts = Counter(a["status"] for a in apps)
    rc = readiness_context(me)
    rcounts = Counter(r["label"] for r in rc["assessed"])
    first = RD.learn_first(rc["assessed"], rc["weights"], rc["hours"], rc["weekly"], rc["skills_of"], top=1)
    return render_template("dashboard.html", eligible=eligible, top=eligible[:3], total=len(opps), apps=apps,
                           upcoming=upcoming, counts=counts, analysis=analysis, statuses=STATUSES,
                           rcounts=rcounts, rlabels=list(RD.LABEL_RANK)[::-1], first=first[0] if first else None)


# ---------------------------------------------------------------- Module 2: discovery
@app.route("/opportunities")
@login_required
def opportunities():
    me = current_student()
    q = request.args.get("q", "").strip().lower()
    typ = request.args.get("type", "")
    loc = request.args.get("location", "")
    skill = request.args.get("skill", "").strip().lower()
    sort = request.args.get("sort", "deadline")
    rows = db.query("SELECT * FROM opportunities")
    out = []
    for o in rows:
        if q and q not in (o["company"] + " " + o["role"]).lower():
            continue
        if typ and o["type"] != typ:
            continue
        if loc and o["location"] != loc:
            continue
        if skill and M.norm_skill(skill) not in M.skill_set(o["skills"]):
            continue
        o["days"] = days_left(o["deadline"])
        o["eligible"], o["reasons"] = M.check_eligibility(me, o)
        out.append(o)
    if sort == "company":
        out.sort(key=lambda o: o["company"])
    else:
        out.sort(key=lambda o: (o["days"] is None or o["days"] < 0, o["days"] if o["days"] is not None else 9999))
    locations = sorted({r["location"] for r in rows})
    saved = {a["opportunity_id"] for a in db.query("SELECT opportunity_id FROM applications WHERE student_id=?", (me["id"],))}
    return render_template("opportunities.html", opps=out, locations=locations, saved=saved,
                           f={"q": request.args.get("q", ""), "type": typ, "location": loc, "skill": skill, "sort": sort})


# ---------------------------------------------------------------- Module 3: matching
@app.route("/matches")
@login_required
def matches():
    me = current_student()
    extra, _ = student_skills_with_resume(me)
    ranked = M.rank(me, db.query("SELECT * FROM opportunities"), extra)
    saved = {a["opportunity_id"] for a in db.query("SELECT opportunity_id FROM applications WHERE student_id=?", (me["id"],))}
    return render_template("matches.html", ranked=ranked, saved=saved, rules=M.__doc__, extra=extra)


# ---------------------------------------------------------------- Module 8: tracker
@app.route("/save/<int:oid>", methods=["POST"])
@login_required
def save_opportunity(oid):
    me = current_student()
    if not db.query("SELECT id FROM applications WHERE student_id=? AND opportunity_id=?", (me["id"], oid), one=True):
        db.execute("INSERT INTO applications (student_id, opportunity_id, status, notes, updated_at) VALUES (?,?,?,?,?)",
                   (me["id"], oid, "Saved", "", datetime.now().isoformat(timespec="seconds")))
        flash("Saved to your tracker.", "ok")
    return redirect(request.referrer or url_for("tracker"))


@app.route("/tracker")
@login_required
def tracker():
    me = current_student()
    apps = db.query("""SELECT a.*, o.company, o.role, o.location, o.deadline, o.apply_link FROM applications a
                       JOIN opportunities o ON o.id=a.opportunity_id WHERE a.student_id=?""", (me["id"],))
    for a in apps:
        a["days"] = days_left(a["deadline"])
    apps.sort(key=lambda a: (a["days"] is None or a["days"] < 0, a["days"] if a["days"] is not None else 9999))
    reminders = [a for a in apps if a["status"] in ("Saved",) and a["days"] is not None and 0 <= a["days"] <= 7]
    return render_template("tracker.html", apps=apps, statuses=STATUSES, reminders=reminders)


@app.route("/tracker/<int:aid>/update", methods=["POST"])
@login_required
def tracker_update(aid):
    me = current_student()
    status = request.form.get("status")
    if status in STATUSES:
        db.execute("UPDATE applications SET status=?, notes=?, updated_at=? WHERE id=? AND student_id=?",
                   (status, request.form.get("notes", ""), datetime.now().isoformat(timespec="seconds"), aid, me["id"]))
        flash("Status updated.", "ok")
    return redirect(url_for("tracker"))


@app.route("/tracker/<int:aid>/delete", methods=["POST"])
@login_required
def tracker_delete(aid):
    db.execute("DELETE FROM applications WHERE id=? AND student_id=?", (aid, current_student()["id"]))
    return redirect(url_for("tracker"))


# ---------------------------------------------------------------- Module 4: resume
@app.route("/resume", methods=["GET", "POST"])
@login_required
def resume_page():
    me = current_student()
    if request.method == "POST":
        f = request.files.get("resume")
        if not f or not f.filename:
            flash("Choose a PDF, DOCX or TXT resume.", "err")
            return redirect(url_for("resume_page"))
        try:
            text = R.extract_text(f)
        except Exception as e:
            flash(f"Could not read that file: {e}", "err")
            return redirect(url_for("resume_page"))
        if len(text.split()) < 20:
            flash("Very little text found - scanned/image PDFs are not supported.", "err")
            return redirect(url_for("resume_page"))
        store = save_analysis(me["id"], R.analyse(text))
        flash(f"Resume analysed and stored in {store}.", "ok")
        return redirect(url_for("resume_page"))
    a = latest_analysis(me["id"])
    new_skills = sorted(set(a["skills"]) - M.skill_set(me["skills"])) if a else []
    return render_template("resume.html", a=a, new_skills=new_skills, mongo=mongo_col() is not None, store_name=SQL_NAME)


@app.route("/resume/apply-skills", methods=["POST"])
@login_required
def resume_apply_skills():
    me = current_student()
    a = latest_analysis(me["id"])
    if a:
        merged = sorted(M.skill_set(me["skills"]) | set(a["skills"]))
        db.execute("UPDATE students SET skills=? WHERE id=?", (", ".join(merged), me["id"]))
        flash("Resume skills added to your profile.", "ok")
    return redirect(url_for("resume_page"))


# ---------------------------------------------------------------- Module 5: skill gap
@app.route("/gap")
@login_required
def gap():
    me = current_student()
    opps = db.query("SELECT * FROM opportunities")
    roles = sorted({o["role"] for o in opps})
    role = request.args.get("role") or (M.split(me["pref_roles"]) or [None])[0]
    selected = next((r for r in roles if role and (role.lower() in r.lower() or r.lower() in role.lower())), None)
    result = None
    if selected:
        role_opps = [o for o in opps if o["role"] == selected]
        freq = Counter(s for o in role_opps for s in {M.norm_skill(x) for x in M.split(o["skills"])})
        required = [s for s, _ in freq.most_common()]
        prof = M.skill_set(me["skills"])
        res, analysis = student_skills_with_resume(me)
        rows = []
        for s in required:
            evidence = [e for e, ok in (("profile", s in prof), ("resume", s in res)) if ok]
            rows.append({"skill": s, "have": bool(evidence), "evidence": evidence,
                         "tip": LEARN_TIPS.get(s, DEFAULT_TIP), "demand": freq[s]})
        have = sum(r["have"] for r in rows)
        result = {"rows": rows, "pct": round(100 * have / len(rows)) if rows else 0, "have": have,
                  "n_opps": len(role_opps), "has_resume": analysis is not None}
    return render_template("gap.html", roles=roles, selected=selected, result=result)


# ---------------------------------------------------------------- Modules 6 & 7: readiness, plan, tests
def readiness_context(me):
    """Evidence weights + readiness of every eligible, still-open opportunity."""
    resume_sk, analysis = student_skills_with_resume(me)
    tested = tested_best(me["id"])
    weights = RD.evidence_weights(M.skill_set(me["skills"]), resume_sk, tested)
    hours = skill_hours()
    weekly = me.get("weekly_hours") or 10
    opps = []
    for o in db.query("SELECT * FROM opportunities"):
        d = days_left(o["deadline"])
        if d is None or d < 0 or not M.check_eligibility(me, o)[0]:
            continue
        opps.append(o)
    skills_of = lambda o: [M.norm_skill(s) for s in M.split(o["skills"])]
    days_of = lambda o: days_left(o["deadline"])
    assessed = RD.assess_all(opps, weights, hours, weekly, days_of, skills_of)
    return {"weights": weights, "hours": hours, "weekly": weekly, "assessed": assessed,
            "skills_of": skills_of, "tested": tested, "has_resume": analysis is not None}


@app.route("/readiness")
@login_required
def readiness_page():
    me = current_student()
    c = readiness_context(me)
    top = RD.learn_first(c["assessed"], c["weights"], c["hours"], c["weekly"], c["skills_of"])
    counts = Counter(r["label"] for r in c["assessed"])
    return render_template("readiness.html", c=c, top=top, counts=counts, labels=list(RD.LABEL_RANK)[::-1],
                           consts=RD, tests=TD.T)


@app.route("/plan")
@login_required
def plan():
    me = current_student()
    c = readiness_context(me)
    p = RD.weekly_plan(c["assessed"], c["weights"], c["hours"], c["weekly"], tests_available=set(TD.T))
    return render_template("plan.html", p=p, c=c)


@app.route("/hours", methods=["GET", "POST"])
@login_required
def hours_page():
    used = sorted({M.norm_skill(s) for o in db.query("SELECT skills FROM opportunities") for s in M.split(o["skills"])})
    if request.method == "POST":
        for s in used:
            raw = request.form.get(f"h_{s}", "").strip()
            try:
                v = float(raw)
            except ValueError:
                continue
            if 0 < v <= 200:
                db.execute("DELETE FROM skill_hours WHERE skill=?", (s,))
                db.execute("INSERT INTO skill_hours (skill, hours) VALUES (?,?)", (s, v))
        flash("Estimated hours saved.", "ok")
        return redirect(url_for("hours_page"))
    return render_template("hours.html", used=used, hours=skill_hours(), defaults=RD.DEFAULT_SKILL_HOURS)


def _shuffled(skill):
    out = []
    for i, (q, ok, wrong) in enumerate(TD.T[skill]):
        opts = [ok] + wrong
        random.Random(f"{skill}-{i}").shuffle(opts)
        out.append({"i": i, "q": q, "opts": opts})
    return out


@app.route("/tests")
@login_required
def tests_home():
    me = current_student()
    return render_template("tests.html", skills=sorted(TD.T), best=tested_best(me["id"]),
                           attempts=test_attempts(me["id"])[:8], mongo=mongo_col("skill_tests") is not None,
                           store_name=SQL_NAME, pass_mark=TD.PASS_MARK, weights=student_weights(me))


def student_weights(me):
    resume_sk, _ = student_skills_with_resume(me)
    return RD.evidence_weights(M.skill_set(me["skills"]), resume_sk, tested_best(me["id"]))


@app.route("/tests/<skill>", methods=["GET", "POST"])
@login_required
def take_test(skill):
    if skill not in TD.T:
        flash("No test for that skill yet.", "warn")
        return redirect(url_for("tests_home"))
    me = current_student()
    qs = _shuffled(skill)
    if request.method == "POST":
        review, score = [], 0
        for q in qs:
            chosen = request.form.get(f"q{q['i']}")
            right = TD.T[skill][q["i"]][1]
            score += chosen == right
            review.append({"q": q["q"], "chosen": chosen, "right": right, "ok": chosen == right})
        store = save_test_attempt(me["id"], skill, score, len(qs))
        pct = round(100 * score / len(qs))
        return render_template("test_result.html", skill=skill, score=score, total=len(qs), pct=pct,
                               passed=pct >= TD.PASS_MARK, review=review, store=store,
                               interview=TD.INTERVIEW.get(skill, []), pass_mark=TD.PASS_MARK)
    return render_template("test_take.html", skill=skill, qs=qs, pass_mark=TD.PASS_MARK)


# ---------------------------------------------------------------- bootstrap
def seed():
    if not db.query("SELECT id FROM opportunities LIMIT 1", one=True):
        for row in sample_opportunities():
            db.execute("""INSERT INTO opportunities (company,role,type,location,skills,min_cgpa,branches,grad_year,
                          stipend,deadline,apply_link,description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", row)
    if not db.query("SELECT id FROM students LIMIT 1", one=True):
        now = datetime.now().isoformat(timespec="seconds")
        demo = [
            ("Aarav Sharma", "aarav@demo.edu", "B.Tech", "Computer Science", 2027, 8.2,
             "python, sql, flask, mysql, git, data structures, oop", "Persistent Systems, Amazon, Infosys",
             "Backend Developer Intern, Software Engineer Intern", "Pune, Hyderabad"),
            ("Diya Patel", "diya@demo.edu", "B.Tech", "Information Technology", 2026, 7.1,
             "java, sql, communication, dbms", "TCS, Capgemini", "Software Engineer, Programmer Analyst Trainee", "Pune, Mumbai"),
        ]
        for d in demo:
            db.execute("""INSERT INTO students (name,email,degree,branch,grad_year,cgpa,skills,pref_companies,
                          pref_roles,pref_locations,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", d + (now,))


def bootstrap():
    db.init_db()
    with app.app_context():
        seed()


if __name__ == "__main__":
    bootstrap()
    print(f"Database backend: {db.BACKEND} | Resume store: {'MongoDB' if mongo_col() is not None else 'SQL table'}")
    app.run(debug=True)
