"""Module 3 - transparent matching rules (no black-box ML).

HARD ELIGIBILITY (all must pass, otherwise the opportunity is 'Not eligible'):
  1. CGPA  >= opportunity.min_cgpa
  2. Branch is in opportunity.branches
  3. Graduation year == opportunity.grad_year

MATCH SCORE (0-100, only for eligible opportunities):
  Skills match        60 pts  = 60 * (required skills the student has / required skills)
  Role preference     15 pts  = 15 if the role title contains one of the preferred roles
  Location preference 15 pts  = 15 if location is preferred
  Company preference  10 pts  = 10 if company is preferred
"""
from skills_data import ALIASES, SKILL_CATALOG

W_SKILL, W_ROLE, W_LOC, W_COMP = 60, 15, 15, 10


def split(csv):
    return [x.strip() for x in (csv or "").replace(";", ",").split(",") if x.strip()]


def norm_skill(s):
    s = s.strip().lower()
    return ALIASES.get(s, s)


def skill_set(csv):
    return {norm_skill(s) for s in split(csv)}


def check_eligibility(student, opp):
    reasons = []
    if (student.get("cgpa") or 0) < (opp.get("min_cgpa") or 0):
        reasons.append(f"CGPA {student.get('cgpa')} is below the required {opp['min_cgpa']}")
    branches = [b.lower() for b in split(opp.get("branches"))]
    if branches and (student.get("branch") or "").lower() not in branches:
        reasons.append(f"Branch '{student.get('branch')}' is not eligible")
    if opp.get("grad_year") and student.get("grad_year") != opp["grad_year"]:
        reasons.append(f"Open to the {opp['grad_year']} batch (you: {student.get('grad_year')})")
    return (not reasons), reasons


def score(student, opp, extra_skills=()):
    have = skill_set(student.get("skills")) | set(extra_skills)
    need = [norm_skill(s) for s in split(opp.get("skills"))]
    matched = [s for s in need if s in have]
    missing = [s for s in need if s not in have]
    skill_pts = W_SKILL * (len(matched) / len(need)) if need else W_SKILL

    roles = [r.lower() for r in split(student.get("pref_roles"))]
    role_hit = any(r in opp["role"].lower() or opp["role"].lower() in r for r in roles)
    locs = [l.lower() for l in split(student.get("pref_locations"))]
    loc_hit = opp["location"].lower() in locs
    comps = [c.lower() for c in split(student.get("pref_companies"))]
    comp_hit = opp["company"].lower() in comps

    total = skill_pts + (W_ROLE if role_hit else 0) + (W_LOC if loc_hit else 0) + (W_COMP if comp_hit else 0)
    ok, reasons = check_eligibility(student, opp)
    return {
        "opp": opp, "eligible": ok, "reasons": reasons, "score": round(total),
        "matched": matched, "missing": missing,
        "breakdown": [
            ("Skills match", round(skill_pts), W_SKILL, f"{len(matched)}/{len(need)} required skills"),
            ("Role preference", W_ROLE if role_hit else 0, W_ROLE, "matches a preferred role" if role_hit else "not a preferred role"),
            ("Location preference", W_LOC if loc_hit else 0, W_LOC, "preferred location" if loc_hit else "not a preferred location"),
            ("Company preference", W_COMP if comp_hit else 0, W_COMP, "preferred company" if comp_hit else "not a preferred company"),
        ],
    }


def rank(student, opps, extra_skills=()):
    results = [score(student, o, extra_skills) for o in opps]
    results.sort(key=lambda r: (not r["eligible"], -r["score"]))
    return results
