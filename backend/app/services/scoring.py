"""
Match Scoring Service - Computes match % based on skills, experience, education.

Scoring Logic (explained in comments):
- Skill Overlap: % of JD required skills found in resume
- Experience Relevance: heuristic based on years/role keywords
- Education Match: presence of degree/education keywords from JD
- Final Score: weighted average (skills 50%, experience 35%, education 15%)
"""

import re
from typing import Dict, List, Set, Tuple

from app.services.parser import DocumentParser


class MatchScoringService:
    """Calculate match score between resume and job description."""

    # Weights for final score (must sum to 1.0)
    WEIGHT_SKILLS = 0.50
    WEIGHT_EXPERIENCE = 0.35
    WEIGHT_EDUCATION = 0.15

    def __init__(self):
        self._parser = DocumentParser()

    def compute_analysis(
        self,
        resume_text: str,
        jd_text: str,
    ) -> Tuple[float, List[str], List[str], List[str], List[str], List[str]]:
        """
        Compute full match analysis.
        
        Returns: (match_score, strengths, gaps, key_insights, skill_overlap, missing_skills)
        """
        resume_data = self._parser.parse_resume_structured(resume_text)
        jd_data = self._parser.parse_jd_structured(jd_text)

        resume_skills = self._normalize_skills(resume_data["skills"])
        jd_skills = self._normalize_skills(jd_data["required_skills"])

        # Skill overlap: JD skills found in resume
        overlap = resume_skills & jd_skills
        missing = jd_skills - resume_skills
        skill_score = len(overlap) / len(jd_skills) if jd_skills else 1.0

        # Experience relevance: keyword and structure heuristic
        exp_score = self._experience_score(resume_data["experience"], jd_data["experience_requirements"])

        # Education match: degree/qualification keywords
        edu_score = self._education_score(resume_data["education"], jd_data["education_requirements"], jd_text)

        # Final weighted score (0-100)
        total = (
            skill_score * self.WEIGHT_SKILLS
            + exp_score * self.WEIGHT_EXPERIENCE
            + edu_score * self.WEIGHT_EDUCATION
        )
        match_score = round(min(100, total * 100), 1)

        strengths = self._build_strengths(overlap, resume_data, jd_text)
        gaps = self._build_gaps(missing, jd_data)
        key_insights = self._build_insights(resume_data, jd_data, match_score)

        skill_overlap_list = [s.title() for s in list(overlap)[:10]]
        missing_skills_list = [s.title() for s in list(missing)[:10]]
        return match_score, strengths, gaps, key_insights, skill_overlap_list, missing_skills_list

    def _normalize_skills(self, skills: List[str]) -> Set[str]:
        """Normalize skill names for comparison (lowercase, strip)."""
        out = set()
        for s in skills:
            t = re.sub(r"[^\w\s]", "", s.lower()).strip()
            if len(t) >= 2:
                out.add(t)
        return out

    def _experience_score(self, resume_exp: List[str], jd_exp: List[str]) -> float:
        """
        Heuristic: presence of years, role titles, tech stack in resume.
        Score 0-1 based on how much JD experience requirements appear in resume.
        """
        if not jd_exp:
            return 1.0
        jd_text = " ".join(jd_exp).lower()
        resume_text = " ".join(resume_exp).lower()

        # Check for years of experience (e.g., "5+ years", "3-5 years")
        years_match = re.search(r"(\d+)\+?\s*years?", jd_text)
        score = 0.5  # Base
        if years_match:
            req_years = int(years_match.group(1))
            res_years = re.findall(r"(\d+)\+?\s*years?", resume_text)
            if res_years and max(int(y) for y in res_years) >= req_years:
                score += 0.3
        # Keyword overlap
        jd_words = set(re.findall(r"\b\w{4,}\b", jd_text))
        res_words = set(re.findall(r"\b\w{4,}\b", resume_text))
        overlap = len(jd_words & res_words) / max(len(jd_words), 1)
        score = min(1.0, score + overlap * 0.2)
        return score

    def _education_score(
        self,
        resume_edu: List[str],
        jd_edu: List[str],
        jd_full: str,
    ) -> float:
        """
        Education match: degree, university keywords from JD found in resume.
        """
        resume_text = " ".join(resume_edu).lower()
        edu_keywords = {"bachelor", "bsc", "bs ", "ms ", "masters", "phd", "degree", "graduation", "university", "college", "state university", "suny", "ivy"}
        jd_lower = jd_full.lower()
        required = []
        for w in edu_keywords:
            if w in jd_lower:
                required.append(w)
        if not required:
            return 1.0
        found = sum(1 for w in required if w in resume_text)
        return min(1.0, found / len(required))

    def _build_strengths(
        self,
        overlap: Set[str],
        resume_data: Dict,
        jd_text: str,
    ) -> List[str]:
        """Build list of strengths from skill overlap and resume content."""
        strengths = []
        for s in list(overlap)[:10]:
            strengths.append(f"Has required skill: {s.title()}")
        if resume_data["experience"]:
            strengths.append("Has relevant work experience")
        if resume_data["education"]:
            strengths.append("Has education/qualifications listed")
        return strengths[:8]

    def _build_gaps(
        self,
        missing: Set[str],
        jd_data: Dict,
    ) -> List[str]:
        """Build list of gaps (missing skills)."""
        gaps = [f"Missing skill: {s.title()}" for s in list(missing)[:10]]
        return gaps[:8]

    def _build_insights(
        self,
        resume_data: Dict,
        jd_data: Dict,
        match_score: float,
    ) -> List[str]:
        """Build key insights."""
        insights = []
        insights.append(f"Overall match: {match_score}%")
        if resume_data["skills"]:
            insights.append(f"Resume lists {len(resume_data['skills'])} skills")
        if jd_data["required_skills"]:
            insights.append(f"Job requires {len(jd_data['required_skills'])} skill areas")
        return insights[:5]
