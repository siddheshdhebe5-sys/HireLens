"""Skill and Keyword Extraction Service.

Uses an extensible dictionary and regex word-boundary matching to deterministically
identify technical skills, domain tools, soft skills, and relevant keywords.
"""

import re
from typing import Dict, List, Set, Tuple, Any
from collections import Counter


class SkillExtractor:
    """Deterministic extractor for technical, data, cloud, and professional skills."""

    SKILL_DATABASE: Dict[str, Dict[str, Any]] = {
        # Programming Languages
        "Python": {"category": "Programming Languages", "pattern": r"\bpython\b"},
        "C": {"category": "Programming Languages", "pattern": r"\bC\b(?!\s*[\+#])"},
        "C++": {"category": "Programming Languages", "pattern": r"\bC\+\+\b"},
        "C#": {"category": "Programming Languages", "pattern": r"\bC#\b|\bc\s*sharp\b"},
        "Java": {"category": "Programming Languages", "pattern": r"\bjava\b(?!script)"},
        "JavaScript": {"category": "Programming Languages", "pattern": r"\bjavascript\b|\bjs\b"},
        "TypeScript": {"category": "Programming Languages", "pattern": r"\btypescript\b|\bts\b"},
        "Go": {"category": "Programming Languages", "pattern": r"\bgolang\b|\bgo\b(?!ing|es|ne)"},
        "Rust": {"category": "Programming Languages", "pattern": r"\brust\b"},
        "PHP": {"category": "Programming Languages", "pattern": r"\bphp\b"},
        "Ruby": {"category": "Programming Languages", "pattern": r"\bruby\b"},
        "Swift": {"category": "Programming Languages", "pattern": r"\bswift\b"},
        "Kotlin": {"category": "Programming Languages", "pattern": r"\bkotlin\b"},
        "R": {"category": "Programming Languages", "pattern": r"\bR\b(?=\s+programming|\s+language|\s*[\,\;]|$)"},
        "SQL": {"category": "Programming Languages", "pattern": r"\bsql\b"},
        "HTML": {"category": "Programming Languages", "pattern": r"\bhtml5?\b"},
        "CSS": {"category": "Programming Languages", "pattern": r"\bcss3?\b"},
        "Shell / Bash": {"category": "Programming Languages", "pattern": r"\b(bash|shell\s*scripting|zsh)\b"},

        # Data Science, ML & Analytics
        "Data Science": {"category": "Data & AI", "pattern": r"\bdata\s*science\b"},
        "Data Analysis": {"category": "Data & AI", "pattern": r"\bdata\s*analysis\b|\bdata\s*analytics\b"},
        "Data Visualization": {"category": "Data & AI", "pattern": r"\bdata\s*visualization\b"},
        "Machine Learning": {"category": "Data & AI", "pattern": r"\bmachine\s*learning\b|\bml\b"},
        "Deep Learning": {"category": "Data & AI", "pattern": r"\bdeep\s*learning\b"},
        "Statistics": {"category": "Data & AI", "pattern": r"\bstatistics\b|\bstatistical\s*analysis\b"},
        "Pandas": {"category": "Data & AI", "pattern": r"\bpandas\b"},
        "NumPy": {"category": "Data & AI", "pattern": r"\bnumpy\b"},
        "Scikit-learn": {"category": "Data & AI", "pattern": r"\bscikit[\s\-_]*learn\b|\bsklearn\b"},
        "TensorFlow": {"category": "Data & AI", "pattern": r"\btensorflow\b|\btf\b"},
        "PyTorch": {"category": "Data & AI", "pattern": r"\bpytorch\b"},
        "Excel": {"category": "Data & AI", "pattern": r"\b(ms\s*)?excel\b|\badvanced\s*excel\b|\bspreadsheets?\b"},
        "Power BI": {"category": "Data & AI", "pattern": r"\bpower\s*bi\b"},
        "Tableau": {"category": "Data & AI", "pattern": r"\btableau\b"},
        "Matplotlib": {"category": "Data & AI", "pattern": r"\bmatplotlib\b"},
        "Seaborn": {"category": "Data & AI", "pattern": r"\bseaborn\b"},
        "Natural Language Processing (NLP)": {"category": "Data & AI", "pattern": r"\bnlp\b|\bnatural\s*language\s*processing\b"},
        "Computer Vision": {"category": "Data & AI", "pattern": r"\bcomputer\s*vision\b|\bopencv\b"},
        "Generative AI / LLMs": {"category": "Data & AI", "pattern": r"\bgenerative\s*ai\b|\bgenai\b|\bllms?\b|\blarge\s*language\s*models?\b"},
        "Big Data": {"category": "Data & AI", "pattern": r"\bbig\s*data\b|\bspark\b|\bhadoop\b"},

        # Web & Backend Frameworks
        "React": {"category": "Web & Frameworks", "pattern": r"\breact(\.js)?\b"},
        "Next.js": {"category": "Web & Frameworks", "pattern": r"\bnext(\.js)?\b"},
        "Node.js": {"category": "Web & Frameworks", "pattern": r"\bnode(\.js)?\b"},
        "Express": {"category": "Web & Frameworks", "pattern": r"\bexpress(\.js)?\b"},
        "Flask": {"category": "Web & Frameworks", "pattern": r"\bflask\b"},
        "Django": {"category": "Web & Frameworks", "pattern": r"\bdjango\b"},
        "FastAPI": {"category": "Web & Frameworks", "pattern": r"\bfastapi\b"},
        "Spring Boot": {"category": "Web & Frameworks", "pattern": r"\bspring(\s*boot)?\b"},
        "REST API": {"category": "Web & Frameworks", "pattern": r"\brest(ful)?\s*apis?\b"},
        "GraphQL": {"category": "Web & Frameworks", "pattern": r"\bgraphql\b"},
        "Tailwind CSS": {"category": "Web & Frameworks", "pattern": r"\btailwind(\s*css)?\b"},
        "Bootstrap": {"category": "Web & Frameworks", "pattern": r"\bbootstrap\b"},

        # Databases & Cloud / DevOps
        "MySQL": {"category": "Databases & Cloud", "pattern": r"\bmysql\b"},
        "PostgreSQL": {"category": "Databases & Cloud", "pattern": r"\bpostgres(ql)?\b"},
        "MongoDB": {"category": "Databases & Cloud", "pattern": r"\bmongodb\b|\bmongo\b"},
        "Redis": {"category": "Databases & Cloud", "pattern": r"\bredis\b"},
        "AWS": {"category": "Databases & Cloud", "pattern": r"\baws\b|\bamazon\s*web\s*services\b"},
        "Azure": {"category": "Databases & Cloud", "pattern": r"\b(microsoft\s*)?azure\b"},
        "Google Cloud (GCP)": {"category": "Databases & Cloud", "pattern": r"\bgcp\b|\bgoogle\s*cloud\b"},
        "Docker": {"category": "Databases & Cloud", "pattern": r"\bdocker\b"},
        "Kubernetes": {"category": "Databases & Cloud", "pattern": r"\bkubernetes\b|\bk8s\b"},
        "CI/CD": {"category": "Databases & Cloud", "pattern": r"\bci\s*/\s*cd\b|\bcontinuous\s*integration\b"},
        "Linux": {"category": "Databases & Cloud", "pattern": r"\blinux\b|\bunix\b"},

        # Tools & Methodologies
        "Git": {"category": "Tools & Methods", "pattern": r"\bgit\b"},
        "GitHub": {"category": "Tools & Methods", "pattern": r"\bgithub\b"},
        "GitLab": {"category": "Tools & Methods", "pattern": r"\bgitlab\b"},
        "Jira": {"category": "Tools & Methods", "pattern": r"\bjira\b"},
        "Agile": {"category": "Tools & Methods", "pattern": r"\bagile\b|\bscrum\b"},
        "Postman": {"category": "Tools & Methods", "pattern": r"\bpostman\b"},
        "Figma": {"category": "Tools & Methods", "pattern": r"\bfigma\b"},
        "Jupyter": {"category": "Tools & Methods", "pattern": r"\bjupyter(\s*notebook)?\b"},
        "Unit Testing": {"category": "Tools & Methods", "pattern": r"\bunit\s*testing\b|\bpytest\b|\bjunit\b|\btdd\b"},

        # Professional & Soft Skills
        "Communication": {"category": "Professional Skills", "pattern": r"\bcommunication(\s*skills)?\b|\bwritten\s*and\s*verbal\b"},
        "Leadership": {"category": "Professional Skills", "pattern": r"\bleadership\b|\bmentoring\b|\bteam\s*lead\b"},
        "Problem Solving": {"category": "Professional Skills", "pattern": r"\bproblem\s*solving\b|\banalytical\s*thinking\b"},
        "Teamwork": {"category": "Professional Skills", "pattern": r"\bteamwork\b|\bcollaboration\b|\bcross[\s\-_]*functional\b"},
        "Time Management": {"category": "Professional Skills", "pattern": r"\btime\s*management\b|\borganization(al)?\s*skills?\b"},
        "Critical Thinking": {"category": "Professional Skills", "pattern": r"\bcritical\s*thinking\b"},
        "Project Management": {"category": "Professional Skills", "pattern": r"\bproject\s*management\b"},
        "Adaptability": {"category": "Professional Skills", "pattern": r"\badaptability\b|\bfast\s*learner\b"}
    }

    # Common English and job-posting stopwords for keyword analysis
    STOPWORDS: Set[str] = {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t',
        'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
        'can', 'can\'t', 'cannot', 'could', 'did', 'do', 'does', 'doing', 'don\'t', 'down', 'during',
        'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here',
        'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its',
        'itself', 'let\'s', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on',
        'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same',
        'she', 'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves',
        'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
        'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with',
        'would', 'you', 'your', 'yours', 'yourself', 'yourselves', 'will', 'job', 'role', 'work', 'working',
        'company', 'team', 'looking', 'candidate', 'apply', 'seeking', 'position', 'requirements', 'responsibilities'
    }

    @classmethod
    def extract_skills(cls, text: str) -> List[Dict[str, str]]:
        """Extracts matched predefined skills along with their categories."""
        if not text:
            return []

        found_skills: List[Dict[str, str]] = []
        for skill_name, meta in cls.SKILL_DATABASE.items():
            pattern = meta["pattern"]
            flags = re.IGNORECASE
            if re.search(pattern, text, flags):
                found_skills.append({
                    "name": skill_name,
                    "category": meta["category"]
                })

        return sorted(found_skills, key=lambda x: (x["category"], x["name"]))

    @classmethod
    def extract_skill_names(cls, text: str) -> Set[str]:
        """Extracts a simple set of matched skill names."""
        skills = cls.extract_skills(text)
        return {s["name"] for s in skills}

    @classmethod
    def add_custom_skill(cls, name: str, category: str, pattern: str) -> None:
        """Dynamically add or override a skill in the dictionary."""
        cls.SKILL_DATABASE[name] = {
            "category": category,
            "pattern": pattern
        }

    @classmethod
    def extract_keywords(cls, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """Extracts top meaningful domain keywords and frequencies, ignoring common stopwords."""
        if not text:
            return []

        words = re.findall(r'\b[A-Za-z][A-Za-z0-9+#.-]{1,25}\b', text.lower())
        filtered = [w for w in words if w not in cls.STOPWORDS and len(w) > 2]
        counts = Counter(filtered)
        return counts.most_common(top_n)

    @classmethod
    def extract_job_metadata(cls, text: str) -> Dict[str, Any]:
        """Extracts job title, company name, and key requirements heuristically."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        title = None
        company = None

        for line in lines[:8]:
            title_match = re.search(r'(?:job\s*title|position|role)\s*:\s*(.+)$', line, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                break

        for line in lines[:8]:
            company_match = re.search(r'(?:company|organization|employer)\s*:\s*(.+)$', line, re.IGNORECASE)
            if company_match:
                company = company_match.group(1).strip()
                break

        # Fallback heuristic if not explicitly labeled
        if not title and lines:
            # Often first line is the role title if short
            if len(lines[0]) < 60 and not re.search(r'http|about|summary|overview', lines[0], re.IGNORECASE):
                title = lines[0]

        return {
            "title": title or "Target Role",
            "company": company or "Hiring Team",
            "extracted_skills": cls.extract_skills(text)
        }
