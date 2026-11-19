"""Module 4 - resume parsing and structured feedback (rule-based, explainable)."""
import re
from datetime import datetime
from skills_data import SKILL_CATALOG, ALIASES

SECTIONS = {
    "Education": r"\beducation\b|\bacademic",
    "Skills": r"\bskills\b|technical skills",
    "Projects": r"\bprojects?\b",
    "Experience": r"\bexperience\b|\binternships?\b|work history",
    "Certifications": r"\bcertifications?\b|\bcourses?\b",
    "Achievements": r"\bachievements?\b|\bawards?\b|\bhonou?rs\b",
}
ACTION_VERBS = ["built", "developed", "designed", "implemented", "created", "led", "optimized",
                "optimised", "deployed", "automated", "improved", "analysed", "analyzed", "managed", "reduced", "increased"]


def extract_text(file_storage):
    name = (file_storage.filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(file_storage.stream).pages)
    if name.endswith(".docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(file_storage.stream).paragraphs)
    return file_storage.read().decode("utf-8", errors="ignore")


def _has_skill(text, skill):
    pattern = r"(?<![A-Za-z0-9+#])" + re.escape(skill) + r"(?![A-Za-z0-9+#])"
    return re.search(pattern, text, re.I) is not None


def detect_skills(text):
    found = {s for s in SKILL_CATALOG if _has_skill(text, s)}
    for alias, canon in ALIASES.items():
        if len(alias) > 2 and _has_skill(text, alias):
            found.add(canon)
    return sorted(found)


def analyse(text):
    t = text or ""
    words = len(t.split())
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", t)
    phone = re.search(r"(\+?\d[\d\s-]{8,13}\d)", t)
    links = {"LinkedIn": "linkedin.com" in t.lower(), "GitHub": "github.com" in t.lower()}
    sections = {k: bool(re.search(v, t, re.I)) for k, v in SECTIONS.items()}
    skills = detect_skills(t)
    verbs = sorted({v for v in ACTION_VERBS if re.search(rf"\b{v}\b", t, re.I)})
    numbers = len(re.findall(r"\d+\s?%|\b\d{2,}\+?\b", t))

    score, feedback = 0, []

    def add(ok, pts, good, bad):
        nonlocal score
        if ok:
            score += pts
            feedback.append(("good", good))
        else:
            feedback.append(("fix", bad))

    add(bool(email) and bool(phone), 12, "Contact details (email and phone) found.", "Add a professional email and phone number at the top.")
    add(any(links.values()), 5, "Profile links found (" + ", ".join(k for k, v in links.items() if v) + ").", "Add your GitHub and LinkedIn links.")
    for name in ["Education", "Skills", "Projects"]:
        add(sections[name], 8, f"{name} section present.", f"Add a clear '{name}' section.")
    add(sections["Experience"], 8, "Experience / internships section present.", "Add internships, training or open-source work, or a Projects section that shows hands-on work.")
    add(sections["Certifications"] or sections["Achievements"], 6, "Certifications / achievements listed.", "Add certifications, hackathons or achievements.")
    add(len(skills) >= 8, 15, f"{len(skills)} recognised technical skills.", f"Only {len(skills)} recognised skills; list more relevant tools and languages.")
    add(len(verbs) >= 4, 10, "Good use of action verbs (" + ", ".join(verbs[:5]) + ").", "Start bullets with action verbs such as Built, Developed, Optimised.")
    add(numbers >= 3, 10, "Achievements are quantified with numbers.", "Quantify impact (e.g. 'reduced load time by 30%', 'served 200+ users').")
    add(250 <= words <= 900, 10, f"Length looks right ({words} words).", f"Resume is {words} words; aim for 250-900 (one page for freshers).")

    score = min(score, 100)
    return {
        "score": score, "word_count": words, "email": email.group(0) if email else None,
        "skills": skills, "sections": sections, "feedback": feedback,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
