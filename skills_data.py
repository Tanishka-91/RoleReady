"""Skill catalogue, aliases, learning tips and sample data for the demo."""
from datetime import date, timedelta

SKILL_CATALOG = [
    "python", "java", "c", "c++", "c#", "javascript", "typescript", "sql", "html", "css", "react",
    "node.js", "flask", "django", "spring boot", "mysql", "mongodb", "postgresql", "git", "github",
    "docker", "kubernetes", "aws", "azure", "linux", "rest api", "data structures", "algorithms",
    "oop", "dbms", "operating systems", "computer networks", "machine learning", "deep learning",
    "nlp", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "power bi", "tableau",
    "excel", "statistics", "data analysis", "selenium", "testing", "system design", "agile",
    "figma", "ui/ux", "communication", "problem solving", "android", "kotlin", "devops", "ci/cd",
    "cybersecurity", "networking",
]

ALIASES = {
    "js": "javascript", "py": "python", "ml": "machine learning", "dl": "deep learning",
    "reactjs": "react", "react.js": "react", "nodejs": "node.js", "node": "node.js",
    "dsa": "data structures", "data structure": "data structures", "ds": "data structures",
    "algo": "algorithms", "os": "operating systems", "cn": "computer networks",
    "postgres": "postgresql", "mongo": "mongodb", "sklearn": "scikit-learn",
    "restful api": "rest api", "restful apis": "rest api", "apis": "rest api", "api": "rest api",
    "object oriented programming": "oop", "cpp": "c++", "ui ux": "ui/ux", "powerbi": "power bi",
    "springboot": "spring boot", "cicd": "ci/cd", "database": "dbms", "databases": "dbms",
}

LEARN_TIPS = {
    "python": "Solve 20 problems on HackerRank's Python track and build one small Flask/CLI project.",
    "sql": "Practise joins, GROUP BY and subqueries on a sample database; aim for 30 queries.",
    "data structures": "Cover arrays, linked lists, stacks/queues, trees and hash maps; solve 2 problems/day.",
    "algorithms": "Practise sorting, searching, recursion, DP and graph basics on LeetCode (Easy then Medium).",
    "dbms": "Revise normalisation, ER diagrams, transactions and indexing; link it to your project schema.",
    "operating systems": "Revise processes, threads, scheduling, deadlocks and memory management.",
    "computer networks": "Revise the OSI/TCP-IP layers, HTTP, DNS and TCP handshake.",
    "oop": "Be able to explain the four pillars with code examples from your own projects.",
    "git": "Practise branching, merging and pull requests on a personal repo.",
    "docker": "Containerise one of your projects with a Dockerfile and docker-compose.",
    "machine learning": "Finish one end-to-end project with scikit-learn: cleaning, training, evaluation.",
    "system design": "Study basics: load balancers, caching, DB sharding; design a URL shortener.",
    "react": "Build a small CRUD front-end using hooks and fetch against a REST API.",
    "rest api": "Build and document a REST API with CRUD endpoints and proper status codes.",
    "aws": "Complete an AWS Cloud Practitioner learning path and deploy a tiny app.",
    "statistics": "Revise distributions, hypothesis testing and regression.",
    "communication": "Record yourself answering 'Tell me about yourself' and refine it.",
}
DEFAULT_TIP = "Take a short course, then apply it in a mini-project you can show on your resume."


def _d(days):
    return (date.today() + timedelta(days=days)).isoformat()


def sample_opportunities():
    ALL = "Computer Science,Information Technology,Electronics,Data Science,AI & ML"
    CS = "Computer Science,Information Technology,AI & ML,Data Science"
    rows = [
        ("Infosys", "Software Engineer Intern", "Internship", "Pune", "python,sql,data structures,oop,dbms", 6.5, ALL, 2027, "Rs 20,000/mo", 9, "Build internal tools with a mentor over 6 months."),
        ("TCS", "Systems Engineer", "Placement", "Mumbai", "java,sql,oop,dbms,communication", 6.0, ALL, 2026, "Rs 7 LPA", 20, "Campus drive: aptitude + technical + HR."),
        ("Wipro", "Project Engineer", "Placement", "Bengaluru", "java,sql,data structures,problem solving", 6.0, ALL, 2026, "Rs 6.5 LPA", 14, "Elite NTH hiring programme."),
        ("Zoho", "Software Developer", "Placement", "Chennai", "c,data structures,algorithms,problem solving", 7.0, CS, 2026, "Rs 8 LPA", 30, "Multiple coding rounds, strong DSA focus."),
        ("Persistent Systems", "Backend Developer Intern", "Internship", "Pune", "python,flask,mysql,rest api,git", 7.0, CS, 2027, "Rs 25,000/mo", 12, "Work on microservices in the product engineering team."),
        ("Amazon", "SDE Intern", "Internship", "Hyderabad", "data structures,algorithms,java,system design,problem solving", 7.5, CS, 2027, "Rs 80,000/mo", 6, "Highly competitive; strong DSA and CS fundamentals required."),
        ("Accenture", "Associate Software Engineer", "Placement", "Pune", "java,sql,communication,problem solving,dbms", 6.0, ALL, 2026, "Rs 4.5 LPA", 25, "Mass hiring for consulting and delivery roles."),
        ("Deloitte", "Data Analyst Intern", "Internship", "Mumbai", "sql,excel,power bi,data analysis,statistics", 7.0, "Computer Science,Information Technology,Data Science,AI & ML", 2027, "Rs 18,000/mo", 18, "Analytics for audit and consulting clients."),
        ("Mu Sigma", "Decision Scientist Trainee", "Placement", "Bengaluru", "python,sql,statistics,machine learning,data analysis", 6.5, CS, 2026, "Rs 6 LPA", 40, "Analytical problem solving with data."),
        ("Capgemini", "Full Stack Developer", "Placement", "Pune", "javascript,react,node.js,mongodb,rest api,git", 6.0, CS, 2026, "Rs 5 LPA", 16, "Build web applications end to end."),
        ("Cognizant", "Programmer Analyst Trainee", "Placement", "Pune", "java,sql,oop,communication", 6.0, ALL, 2026, "Rs 4 LPA", 3, "GenC hiring programme."),
        ("Tech Mahindra", "Cloud Support Intern", "Internship", "Pune", "linux,aws,computer networks,python,git", 6.0, ALL, 2027, "Rs 15,000/mo", 22, "Support cloud infrastructure for telecom clients."),
        ("Flipkart", "Machine Learning Intern", "Internship", "Bengaluru", "python,machine learning,pandas,numpy,statistics,scikit-learn", 8.0, "Computer Science,Data Science,AI & ML", 2027, "Rs 60,000/mo", 28, "Work on recommendation and ranking systems."),
        ("Cisco", "Network Engineer Intern", "Internship", "Bengaluru", "computer networks,linux,python,networking", 7.0, "Computer Science,Information Technology,Electronics", 2027, "Rs 40,000/mo", 35, "Automate network testing."),
        ("Thoughtworks", "Frontend Developer Intern", "Internship", "Pune", "javascript,react,html,css,git,testing", 7.0, CS, 2027, "Rs 30,000/mo", 10, "Agile team, pair programming culture."),
        ("Bosch", "Embedded Software Intern", "Internship", "Coimbatore", "c,c++,operating systems,problem solving", 7.0, "Electronics,Computer Science", 2027, "Rs 25,000/mo", 45, "Firmware development for automotive systems."),
    ]
    out = []
    for i, (co, role, typ, loc, sk, cg, br, yr, pay, dl, desc) in enumerate(rows, 1):
        out.append((co, role, typ, loc, sk, cg, br, yr, pay, _d(dl),
                    f"https://careers.example.com/{co.lower().replace(' ', '-')}/{i}", desc))
    return out
