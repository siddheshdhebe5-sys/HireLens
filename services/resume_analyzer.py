"""Resume Analyzer Service.

Calculates multi-factor, explainable ATS-style resume-job alignment scores,
categorizes skill matches/gaps, and produces actionable recommendations.
"""

import math
import re
from typing import Dict, Any, List, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from services.skill_extractor import SkillExtractor


class ResumeAnalyzer:
    """Calculates alignment metrics between candidate resume and target job description."""

    ACTION_VERBS = {
        'developed', 'engineered', 'built', 'created', 'implemented', 'designed',
        'analyzed', 'optimized', 'led', 'managed', 'collaborated', 'programmed',
        'researched', 'streamlined', 'deployed', 'automated', 'delivered', 'improved',
        'formulated', 'trained', 'mentored', 'orchestrated', 'conducted', 'integrated'
    }

    @classmethod
    def analyze(cls, resume_data: Dict[str, Any], job_text: str) -> Dict[str, Any]:
        """Performs full comparative analysis between parsed resume and job posting."""
        resume_raw = resume_data.get("raw_text", "")
        if not resume_raw.strip() or not job_text.strip():
            raise ValueError("Both resume text and job description must be non-empty.")

        # 1. Skill Extraction
        resume_skills_list = SkillExtractor.extract_skills(resume_raw)
        job_skills_list = SkillExtractor.extract_skills(job_text)

        resume_skill_names: Set[str] = {s["name"] for s in resume_skills_list}
        job_skill_names: Set[str] = {s["name"] for s in job_skills_list}

        matched_skill_names = resume_skill_names.intersection(job_skill_names)
        missing_skill_names = job_skill_names - resume_skill_names
        extra_skill_names = resume_skill_names - job_skill_names

        matched_skills = [s for s in job_skills_list if s["name"] in matched_skill_names]
        missing_skills = [s for s in job_skills_list if s["name"] in missing_skill_names]
        extra_skills = [s for s in resume_skills_list if s["name"] in extra_skill_names]

        # 2. Sub-Score 1: Skill Match Score (40% weight)
        if job_skill_names:
            skill_match_ratio = len(matched_skill_names) / len(job_skill_names)
        else:
            # If no predefined skills in job desc, base on keyword overlap
            skill_match_ratio = 0.70
        skill_score = min(100.0, max(0.0, skill_match_ratio * 100))

        # 3. Sub-Score 2: Keyword Alignment Score (25% weight)
        job_keywords = SkillExtractor.extract_keywords(job_text, top_n=25)
        resume_text_lower = resume_raw.lower()
        matched_keywords = []
        missing_keywords = []

        for kw, freq in job_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', resume_text_lower):
                matched_keywords.append({"keyword": kw, "job_frequency": freq, "in_resume": True})
            else:
                missing_keywords.append({"keyword": kw, "job_frequency": freq, "in_resume": False})

        if job_keywords:
            keyword_match_ratio = len(matched_keywords) / len(job_keywords)
        else:
            keyword_match_ratio = 0.75
        keyword_score = min(100.0, max(0.0, keyword_match_ratio * 100))

        # 4. Sub-Score 3: Semantic TF-IDF Cosine Similarity (20% weight)
        semantic_score = cls._calculate_semantic_similarity(resume_raw, job_text)

        # 5. Sub-Score 4: Experience & Action Evidence (15% weight)
        evidence_score = cls._calculate_evidence_score(resume_raw, resume_data.get("sections", {}))

        # Weighted Combined Alignment Score
        weighted_total = (
            (skill_score * 0.40) +
            (keyword_score * 0.25) +
            (semantic_score * 0.20) +
            (evidence_score * 0.15)
        )
        final_score = int(round(weighted_total))
        final_score = max(5, min(98, final_score))  # Realistic bounds

        # Determine Score Rating Tier
        if final_score >= 80:
            score_tier = "High Alignment"
            score_color = "success"
            score_summary = "Your resume strongly mirrors the key qualifications and terminology required for this position."
        elif final_score >= 60:
            score_tier = "Moderate Alignment"
            score_color = "warning"
            score_summary = "Good foundation, but several notable skills and keywords from the job description are currently missing."
        else:
            score_tier = "Low Alignment"
            score_color = "danger"
            score_summary = "Significant gaps detected in core technical skills and role-specific requirements."

        # Generate Rule-Based Actionable Recommendations
        recommendations = cls._generate_recommendations(
            missing_skills=missing_skills,
            missing_keywords=missing_keywords,
            evidence_score=evidence_score,
            sections=resume_data.get("sections", {}),
            matched_skills=matched_skills
        )

        job_meta = SkillExtractor.extract_job_metadata(job_text)

        return {
            "score": final_score,
            "score_tier": score_tier,
            "score_color": score_color,
            "score_summary": score_summary,
            "breakdown": {
                "skill_score": int(round(skill_score)),
                "keyword_score": int(round(keyword_score)),
                "semantic_score": int(round(semantic_score)),
                "evidence_score": int(round(evidence_score)),
                "weights": {
                    "skill_weight": "40%",
                    "keyword_weight": "25%",
                    "semantic_weight": "20%",
                    "evidence_weight": "15%"
                }
            },
            "skills": {
                "matched": matched_skills,
                "missing": missing_skills,
                "extra": extra_skills,
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills),
                "total_job_skills": len(job_skills_list)
            },
            "keywords": {
                "matched": matched_keywords[:12],
                "missing": missing_keywords[:12],
                "top_job_keywords": job_keywords[:15]
            },
            "job_meta": job_meta,
            "recommendations": recommendations,
            "disclaimer": (
                "Resume-Job Alignment Score: This is an estimated alignment score based on the "
                "job description and information found in the resume. It is not a guarantee of "
                "ATS screening or interview selection."
            )
        }

    @staticmethod
    def _calculate_semantic_similarity(resume_text: str, job_text: str) -> float:
        """Computes TF-IDF cosine similarity between resume and job description text."""
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=1000
            )
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            # Rescale 0.1 - 0.7 cosine similarity to a 20 - 100 visual score
            rescaled = min(100.0, max(15.0, (similarity * 130)))
            return rescaled
        except Exception:
            return 50.0

    @classmethod
    def _calculate_evidence_score(cls, resume_text: str, sections: Dict[str, str]) -> float:
        """Evaluates quantitative metrics, action verbs, and structured project evidence."""
        score = 40.0
        text_lower = resume_text.lower()

        # 1. Action verbs detection
        verb_count = sum(1 for verb in cls.ACTION_VERBS if re.search(r'\b' + verb + r'\b', text_lower))
        score += min(25.0, verb_count * 3.0)

        # 2. Measurable metrics & numbers (% , $, 10+, 99%)
        metric_matches = re.findall(r'\b(?:\d+[%kM\+]|\$\d+|\d+\s*(?:users|records|students|percent|increase|reduction|uptime))\b', text_lower)
        score += min(20.0, len(metric_matches) * 4.0)

        # 3. Essential sections present
        if sections.get('projects') or sections.get('experience'):
            score += 10.0
        if sections.get('skills'):
            score += 5.0

        return min(100.0, score)

    @staticmethod
    def _generate_recommendations(
        missing_skills: List[Dict[str, str]],
        missing_keywords: List[Dict[str, Any]],
        evidence_score: float,
        sections: Dict[str, str],
        matched_skills: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Generates deterministic, clear recommendations with ethical AI guidelines."""
        recs: List[Dict[str, str]] = []

        # 1. Missing skills advice
        if missing_skills:
            top_missing = [s["name"] for s in missing_skills[:4]]
            missing_str = ", ".join(top_missing)
            recs.append({
                "type": "skills",
                "title": "Incorporate Relevant Missing Skills",
                "badge": "Priority",
                "badge_class": "badge-danger",
                "description": (
                    f"The job posting emphasizes {missing_str}. "
                    "Important: Add these to your resume ONLY if you genuinely possess practical experience or coursework in them. Never fabricate qualifications."
                )
            })

        # 2. Action verbs & metrics
        if evidence_score < 70:
            recs.append({
                "type": "impact",
                "title": "Quantify Impact & Project Metrics",
                "badge": "Content",
                "badge_class": "badge-warning",
                "description": (
                    "Strengthen your project bullet points with measurable outcomes (e.g., 'optimized pipeline by 20%', 'analyzed 1,000+ records'). Use strong action verbs like 'Engineered', 'Analyzed', or 'Orchestrated'."
                )
            })

        # 3. Keyword alignment
        if missing_keywords:
            top_kw = [k["keyword"] for k in missing_keywords[:5]]
            recs.append({
                "type": "keywords",
                "title": "Align Industry Terminology",
                "badge": "ATS Alignment",
                "badge_class": "badge-info",
                "description": (
                    f"Consider organically weaving in relevant job terms such as {', '.join(top_kw)} "
                    "into your project summaries or coursework descriptions where truthful."
                )
            })

        # 4. Summary tailoring
        recs.append({
            "type": "summary",
            "title": "Tailor Your Professional Summary",
            "badge": "Presentation",
            "badge_class": "badge-success",
            "description": (
                "Ensure your top summary highlights your specific interest in this exact role and mirrors the key technical themes found in the job requirements."
            )
        })

        return recs
