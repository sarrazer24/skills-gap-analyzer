"""
Optimized Skill Extractor Module

Extracts skills from text with:
- Fast regex patterns with word boundaries
- Fuzzy matching for variations
- Confidence scoring based on frequency and context
"""

import pandas as pd
import re
from typing import List, Tuple, Optional, Dict, Set
from pathlib import Path
from collections import Counter


class SkillExtractor:
    """Extract skills from documents with high accuracy and confidence scoring"""
    
    def __init__(self, skills_list: List[str], use_llm: bool = False, api_key: Optional[str] = None):
        """
        Initialize SkillExtractor.
        
        Args:
            skills_list: List of skills to search for
            use_llm: Whether to use LLM for enhanced extraction (optional)
            api_key: OpenAI API key if using LLM
        """
        self.skills_list = [s.lower().strip() for s in skills_list if s]
        self.use_llm = use_llm
        self.api_key = api_key
        
        # Build optimized patterns
        self._build_patterns()
        self._build_skill_variations()
    
    def _build_patterns(self):
        """Build compiled regex patterns for fast matching"""
        self.skill_patterns = {}
        
        for skill in self.skills_list:
            # Create pattern with word boundaries to avoid partial matches
            # Escape special regex characters
            escaped = re.escape(skill)
            pattern = re.compile(
                r'\b' + escaped + r'\b',
                re.IGNORECASE | re.MULTILINE
            )
            self.skill_patterns[skill] = pattern
    
    def _build_skill_variations(self):
        """Build common variations of skills (e.g., Node.js -> nodejs, node)"""
        self.variations = {}
        
        for skill in self.skills_list:
            variations = set([skill])
            
            # Add common variations
            # e.g., "machine learning" -> "ml"
            if skill == "machine learning":
                variations.update(["ml", "machine-learning"])
            elif skill == "deep learning":
                variations.update(["dl", "deep-learning"])
            elif skill == "node.js":
                variations.update(["nodejs", "node"])
            elif skill == "c++":
                variations.update(["cpp", "c plus plus"])
            elif skill == "c#":
                variations.update(["csharp", "c sharp"])
            elif skill == "power bi":
                variations.update(["powerbi", "power-bi"])
            elif skill == "power query":
                variations.update(["powerquery", "power-query"])
            
            self.variations[skill] = variations
    
    def _read_pdf(self, file_obj) -> str:
        """Read text from PDF file object"""
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file_obj)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        except ImportError:
            return ""
        except Exception:
            return ""
    
    def _read_docx(self, file_obj) -> str:
        """Read text from DOCX file object"""
        try:
            from docx import Document
            doc = Document(file_obj)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except ImportError:
            return ""
        except Exception:
            return ""
    
    def extract_from_text(self, text: str, return_confidence: bool = False, min_confidence: float = 0.3) -> List[Tuple[str, float]]:
        """
        Extract skills from text with confidence scoring.
        
        Args:
            text: Text to search for skills
            return_confidence: If True, return list of (skill, confidence) tuples
            min_confidence: Minimum confidence threshold (0.0-1.0)
            
        Returns:
            List of skills or list of (skill, confidence) tuples
        """
        if not text or len(text) < 10:
            return []
        
        found_skills = {}
        text_lower = text.lower()
        text_length = len(text)
        
        # Count occurrences of each skill
        for skill, pattern in self.skill_patterns.items():
            matches = pattern.findall(text_lower)
            
            if matches:
                # Calculate confidence based on:
                # 1. Frequency (more mentions = higher confidence)
                # 2. Text density (skill mentions / total words)
                word_count = len(text.split())
                frequency = len(matches)
                density = frequency / max(word_count, 1)
                
                # Confidence formula:
                # Base: 0.5 (found at least once)
                # Frequency boost: up to 0.3 (capped at 5 mentions)
                # Density boost: up to 0.2 (percentage of text)
                base_confidence = 0.5
                frequency_boost = min(0.3, (frequency / 5) * 0.3)
                density_boost = min(0.2, density * 2)
                
                confidence = min(0.95, base_confidence + frequency_boost + density_boost)
                found_skills[skill] = confidence
        
        # Check variations for additional matches (lower confidence)
        for skill in self.skills_list:
            if skill not in found_skills:
                for variant in self.variations.get(skill, set()):
                    if variant != skill:  # Don't match the skill again
                        pattern = re.compile(r'\b' + re.escape(variant) + r'\b', re.IGNORECASE)
                        if pattern.search(text_lower):
                            # Lower confidence for variation matches
                            found_skills[skill] = 0.6
                            break
        
        # Filter by minimum confidence and sort by confidence
        found_skills = {
            skill: conf for skill, conf in found_skills.items()
            if conf >= min_confidence
        }
        
        if return_confidence:
            # Sort by confidence descending
            return sorted(found_skills.items(), key=lambda x: x[1], reverse=True)
        else:
            return list(found_skills.keys())
    
    def extract_batch(self, texts: List[str], return_confidence: bool = False) -> List[List[Tuple[str, float]]]:
        """Extract skills from multiple texts efficiently
        
        Args:
            texts: List of text documents
            return_confidence: Whether to return confidence scores
            
        Returns:
            List of skill lists for each text
        """
        return [self.extract_from_text(text, return_confidence) for text in texts]
    
    def get_skill_profile(self, text: str) -> Dict[str, any]:
        """Get comprehensive skill profile from text
        
        Args:
            text: Text document
            
        Returns:
            Dict with:
            - skills: list of extracted skills
            - confidences: dict of skill -> confidence
            - summary: text summary
            - coverage: percentage of available skills matched
        """
        skills_with_conf = self.extract_from_text(text, return_confidence=True, min_confidence=0.3)
        
        if not skills_with_conf:
            return {
                'skills': [],
                'confidences': {},
                'summary': 'No skills detected',
                'coverage': 0.0
            }
        
        skills = [s for s, c in skills_with_conf]
        confidences = dict(skills_with_conf)
        
        # Calculate coverage
        coverage = len(skills) / len(self.skills_list) if self.skills_list else 0
        
        # Generate summary
        high_conf = [s for s, c in skills_with_conf if c >= 0.7]
        med_conf = [s for s, c in skills_with_conf if 0.5 <= c < 0.7]
        low_conf = [s for s, c in skills_with_conf if 0.3 <= c < 0.5]
        
        summary_parts = []
        if high_conf:
            summary_parts.append(f"Strong: {', '.join(high_conf[:3])}")
        if med_conf:
            summary_parts.append(f"Medium: {', '.join(med_conf[:3])}")
        if low_conf and len(summary_parts) < 2:
            summary_parts.append(f"Mentioned: {', '.join(low_conf[:2])}")
        
        summary = " | ".join(summary_parts) if summary_parts else "Skills detected with low confidence"
        
        return {
            'skills': skills,
            'confidences': confidences,
            'summary': summary,
            'coverage': round(coverage, 2),
            'high_confidence_skills': high_conf,
            'medium_confidence_skills': med_conf,
            'low_confidence_skills': low_conf
        }
