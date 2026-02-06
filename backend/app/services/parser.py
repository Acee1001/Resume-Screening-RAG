"""
Document Parser - Extracts text from PDF and TXT files.

Uses pdfplumber for PDF extraction. Handles both resume and job description parsing.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber


class DocumentParser:
    """Extract and parse text from resume and JD documents."""

    # Common section headers in resumes (for logical chunking)
    RESUME_SECTIONS = [
        r"^(?:professional\s+)?summary|objective|profile$",
        r"^(?:technical\s+)?skills|competencies|expertise$",
        r"^experience|work\s+history|employment$",
        r"^education|academic|qualifications$",
        r"^projects|certifications|achievements$",
    ]

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text from PDF or TXT file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return DocumentParser._extract_from_pdf(file_path)
        elif suffix == ".txt":
            return DocumentParser._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Use PDF or TXT.")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts) if text_parts else ""

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def chunk_resume(self, text: str) -> List[Tuple[str, str]]:
        """
        Chunk resume text into logical sections for RAG retrieval.
        
        Each chunk is (section_name, content). Sections are identified by
        common resume headers. Fallback: chunk by paragraph/sentence.
        
        RAG Flow Step 2: Logical chunking enables precise retrieval.
        """
        text = text.strip()
        if not text:
            return []

        chunks: List[Tuple[str, str]] = []
        lines = text.split("\n")

        current_section = "general"
        current_content: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_content:
                    content = "\n".join(current_content).strip()
                    if content:
                        chunks.append((current_section, content))
                    current_content = []
                continue

            # Check if line is a section header (all caps, short, or matches pattern)
            is_header = (
                len(stripped) < 50
                and (stripped.isupper() or stripped.endswith(":"))
                or any(
                    re.search(pat, stripped, re.I)
                    for pat in self.RESUME_SECTIONS
                )
            )

            if is_header and current_content:
                content = "\n".join(current_content).strip()
                if content:
                    chunks.append((current_section, content))
                current_content = []

            if is_header:
                current_section = re.sub(r"[:]+$", "", stripped.lower()).replace(" ", "_")[:50]
            current_content.append(stripped)

        if current_content:
            content = "\n".join(current_content).strip()
            if content:
                chunks.append((current_section, content))

        # If no sections found, chunk by paragraph (min 100 chars)
        if not chunks and text:
            paragraphs = re.split(r"\n\s*\n", text)
            for i, para in enumerate(paragraphs):
                para = para.strip()
                if len(para) >= 100:
                    chunks.append((f"section_{i}", para))
                elif para:
                    chunks.append((f"section_{i}", para))

        return chunks

    def chunk_jd(self, text: str) -> List[str]:
        """Chunk job description into paragraphs for analysis."""
        text = text.strip()
        if not text:
            return []
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def parse_resume_structured(self, text: str) -> Dict[str, List[str]]:
        """
        Extract structured data from resume for match scoring.
        
        Returns: skills, experience_items, education_items
        """
        chunks = self.chunk_resume(text)
        result: Dict[str, List[str]] = {
            "skills": [],
            "experience": [],
            "education": [],
            "raw_sections": {},
        }

        for section_name, content in chunks:
            result["raw_sections"][section_name] = content

            # Extract skills (common patterns)
            if "skill" in section_name or "competenc" in section_name:
                skills = self._extract_skills(content)
                result["skills"].extend(skills)

            # Extract experience info
            if "experience" in section_name or "work" in section_name or "employment" in section_name:
                result["experience"].append(content)

            # Extract education info
            if "education" in section_name or "academic" in section_name:
                result["education"].append(content)

        # Fallback: scan full text for skills if not found in sections
        if not result["skills"]:
            result["skills"] = self._extract_skills(text)

        return result

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skill-like tokens (comma-separated, bullet items, etc.)."""
        skills = []
        # Comma-separated skills
        for part in re.split(r"[,;|]", text):
            token = part.strip()
            if 2 <= len(token) <= 50 and not token.lower().startswith(("the", "a", "and", "or")):
                skills.append(token)
        # Bullet points
        for line in text.split("\n"):
            line = re.sub(r"^[\-\*•]\s*", "", line.strip())
            if 2 <= len(line) <= 80:
                skills.append(line)
        return list(dict.fromkeys(skills))[:80]  # Dedupe, cap

    def parse_jd_structured(self, text: str) -> Dict[str, List[str]]:
        """Extract required skills and experience from job description."""
        result: Dict[str, List[str]] = {
            "required_skills": [],
            "experience_requirements": [],
            "education_requirements": [],
        }
        skills = self._extract_skills(text)
        result["required_skills"] = skills[:50]
        result["experience_requirements"] = self.chunk_jd(text)
        return result
