"""Readiness-to-deadline engine (the core idea of RoleReady).

Question answered: "Given what a student can PROVE today and the days left before each
deadline, which opportunities can they realistically be ready for, and what should they
learn first?"  Pure functions, no database access, so it is easy to test.

DESIGN CHOICES (our own, adjustable - not empirically derived):
  Evidence weights   self-declared 0.5 | found in resume 0.75 | passed skill test 1.0
  Hours still needed = estimated_hours[skill] * (1 - evidence_weight)
        (a skill you only typed in still needs ~half the hours to be verified/practised)
  Estimates = hours for a student with basics to reach screening-round level in that skill
  Hours available    = weekly_study_hours * days_left / 7
  Label  Ready         needed <= 2 h
         Reachable     needed <= available
         Stretch       needed <= 1.5 x available
         Not feasible  otherwise
Hours per skill are ESTIMATES (editable on the Hours page). 'Reachable' is a planning aid,
not a prediction that the student will be shortlisted or selected.
"""
from skills_data import DEFAULT_TIP, LEARN_TIPS

W_SELF, W_RESUME, W_TESTED = 0.5, 0.75, 1.0
PASS_PCT = 60
READY_HOURS = 2
STRETCH_FACTOR = 1.5
DEFAULT_HOURS = 8
MAX_PLAN_WEEKS = 6
LABEL_RANK = {"Not feasible": 0, "Stretch": 1, "Reachable": 2, "Ready": 3}

# ESTIMATED hours for a student with basics to reach screening-round level (online test / first
# technical round) in each skill. These are assumptions, editable in the app (Hours page).
DEFAULT_SKILL_HOURS = {
    "python": 12, "java": 15, "c": 15, "c++": 15, "sql": 8, "html": 4, "css": 5, "javascript": 12,
    "react": 14, "node.js": 10, "flask": 6, "mysql": 5, "mongodb": 5, "git": 3, "docker": 6,
    "aws": 10, "linux": 6, "rest api": 5, "data structures": 20, "algorithms": 20, "oop": 6,
    "dbms": 8, "operating systems": 10, "computer networks": 8, "machine learning": 20,
    "pandas": 6, "numpy": 4, "scikit-learn": 8, "statistics": 10, "excel": 5, "power bi": 6,
    "data analysis": 10, "system design": 12, "testing": 5, "communication": 5,
    "problem solving": 15, "networking": 8,
}


def evidence_weights(profile_skills, resume_skills, tested):
    """-> {skill: (weight, source)}.  tested = {skill: best score in %}."""
    w = {s: (W_SELF, "self-declared") for s in profile_skills}
    for s in resume_skills:
        if W_RESUME > w.get(s, (0, ""))[0]:
            w[s] = (W_RESUME, "resume")
    for s, pct in tested.items():
        if pct >= PASS_PCT:
            w[s] = (W_TESTED, f"tested {round(pct)}%")
    return w


def label_for(needed, available):
    if needed <= READY_HOURS:
        return "Ready"
    if needed <= available:
        return "Reachable"
    if needed <= STRETCH_FACTOR * available:
        return "Stretch"
    return "Not feasible"


def evaluate(need_skills, weights, hours, weekly_hours, days, override=None):
    """Readiness of ONE opportunity. `override` = {skill: weight} simulates learning a skill."""
    need = list(dict.fromkeys(need_skills))
    rows, needed, wsum = [], 0.0, 0.0
    for s in need:
        w, src = weights.get(s, (0.0, "missing"))
        if override and s in override:
            w, src = override[s], "tested"
        est = hours.get(s, DEFAULT_HOURS)
        left = est * (1 - w)
        needed += left
        wsum += w
        rows.append({"skill": s, "weight": w, "source": src, "est_hours": est, "hours_left": round(left, 1)})
    available = max(weekly_hours, 0) * max(days, 0) / 7
    return {
        "skills": rows, "hours_needed": round(needed, 1), "hours_available": round(available, 1),
        "coverage": round(100 * wsum / len(need)) if need else 100,
        "label": label_for(needed, available),
    }


def assess_all(opps, weights, hours, weekly_hours, days_of, skills_of):
    """Evaluate every opportunity in `opps` (caller passes only eligible, open ones)."""
    out = []
    for o in opps:
        r = evaluate(skills_of(o), weights, hours, weekly_hours, days_of(o))
        r["opp"], r["days"] = o, days_of(o)
        out.append(r)
    out.sort(key=lambda r: (-LABEL_RANK[r["label"]], r["days"]))
    return out


def learn_first(assessed, weights, hours, weekly_hours, skills_of, top=3):
    """Rank skills by how many opportunities they move to a better label, then by coverage gain."""
    cands = {s for r in assessed for s in (x["skill"] for x in r["skills"]) if weights.get(s, (0,))[0] < W_TESTED}
    ranked = []
    for s in cands:
        upgrades, touched, gain = [], 0, 0
        for r in assessed:
            if s not in [x["skill"] for x in r["skills"]]:
                continue
            touched += 1
            sim = evaluate(skills_of(r["opp"]), weights, hours, weekly_hours, r["days"], override={s: W_TESTED})
            gain += sim["coverage"] - r["coverage"]
            if LABEL_RANK[sim["label"]] > LABEL_RANK[r["label"]]:
                upgrades.append((r["opp"]["company"], r["label"], sim["label"]))
        cost = hours.get(s, DEFAULT_HOURS) * (1 - weights.get(s, (0,))[0])
        ranked.append({"skill": s, "opps_touched": touched, "upgrades": upgrades, "gain": gain,
                       "hours": round(cost, 1), "current": weights.get(s, (0, "missing"))[1],
                       "tip": LEARN_TIPS.get(s, DEFAULT_TIP)})
    ranked.sort(key=lambda x: (-len(x["upgrades"]), -x["gain"], x["hours"]))
    return ranked[:top]


def weekly_plan(assessed, weights, hours, weekly_hours, tests_available=()):
    """Order skills by earliest deadline, then by number of opportunities served; pour into weeks."""
    pool = [r for r in assessed if r["label"] != "Not feasible"] or assessed
    skills = {}
    for r in pool:
        for x in r["skills"]:
            if x["hours_left"] <= 0:
                continue
            d = skills.setdefault(x["skill"], {"skill": x["skill"], "hours": x["hours_left"], "opps": [], "first_days": 9999})
            d["opps"].append(r["opp"]["company"])
            d["first_days"] = min(d["first_days"], r["days"])
    order = sorted(skills.values(), key=lambda d: (d["first_days"], -len(d["opps"]), d["hours"]))
    cap = max(float(weekly_hours), 1.0)
    weeks, wk, left = [[]], 0, cap
    leftover = 0.0
    for d in order:
        h = d["hours"]
        while h > 1e-9:
            if wk >= MAX_PLAN_WEEKS:
                leftover += h
                break
            take = min(h, left)
            weeks[wk].append({"skill": d["skill"], "hours": round(take, 1), "opps": d["opps"],
                              "first_days": d["first_days"], "tip": LEARN_TIPS.get(d["skill"], DEFAULT_TIP),
                              "test": d["skill"] in tests_available, "continued": take < d["hours"] - 1e-9})
            h -= take
            left -= take
            if left <= 1e-9:
                wk += 1
                left = cap
                if wk < MAX_PLAN_WEEKS:
                    weeks.append([])
    weeks = [w for w in weeks if w]
    return {"weeks": [{"n": i + 1, "items": w, "hours": round(sum(x["hours"] for x in w), 1)} for i, w in enumerate(weeks)],
            "leftover": round(leftover, 1), "total": round(sum(d["hours"] for d in order), 1)}
