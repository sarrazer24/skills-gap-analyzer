"""Enhanced skill extraction from text, PDF, and DOCX files"""
import re
import os
from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# LLM support (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from io import BytesIO


class SkillExtractor:
    def __init__(self, known_skills: List[str], use_llm: bool = False, api_key: Optional[str] = None):
        """
        Initialize with list of known skills
        
        Args:
            known_skills: List of known skills to match against
            use_llm: Whether to use LLM for extraction (requires OpenAI API key)
            api_key: OpenAI API key (if None, will try to get from OPENAI_API_KEY env var)
        """
        self.known_skills = set(s.lower().strip() for s in known_skills)
        self.skill_aliases = self._build_skill_aliases()
        self._normalize_skills()
        
        # LLM configuration
        self.use_llm = use_llm and OPENAI_AVAILABLE
        if self.use_llm:
            # Get API key from parameter, session state, or environment
            self.api_key = api_key
            if not self.api_key:
                # Try environment variable (reload to get latest)
                self.api_key = os.getenv('OPENAI_API_KEY', '').strip()
            
            # Clean the key (remove any whitespace)
            if self.api_key:
                self.api_key = self.api_key.strip()
            
            if not self.api_key:
                print("⚠️ LLM extraction requested but no API key found. Falling back to pattern matching.")
                self.use_llm = False
            else:
                # Verify key format
                if not self.api_key.startswith('sk-'):
                    print(f"⚠️ API key format looks incorrect (should start with 'sk-'). Falling back to pattern matching.")
                    self.use_llm = False
                else:
                    try:
                        openai.api_key = self.api_key
                    except:
                        # For newer OpenAI client
                        pass
    
    def _build_skill_aliases(self) -> Dict[str, Set[str]]:
        """Build aliases and variations for common skills"""
        aliases = defaultdict(set)
        
        # Programming languages and frameworks
        aliases['python'] = {'python3', 'python 3', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'scipy'}
        aliases['javascript'] = {'js', 'node.js', 'nodejs', 'node', 'typescript', 'ts', 'es6', 'es2015'}
        aliases['java'] = {'java 8', 'java 11', 'spring', 'spring boot', 'springboot', 'hibernate', 'maven'}
        aliases['sql'] = {'mysql', 'postgresql', 'postgres', 'oracle sql', 'mssql', 'sql server', 'sqlite', 'plsql'}
        aliases['machine learning'] = {'ml', 'machine learning', 'deep learning', 'ai', 'artificial intelligence', 'neural networks'}
        aliases['aws'] = {'amazon web services', 'amazon aws', 'aws cloud', 'ec2', 's3', 'lambda', 'rds'}
        aliases['docker'] = {'docker container', 'dockerfile', 'docker compose', 'docker-compose'}
        aliases['kubernetes'] = {'k8s', 'kubernetes', 'kubectl', 'helm'}
        aliases['react'] = {'react.js', 'reactjs', 'react.js', 'redux', 'react native'}
        aliases['git'] = {'git', 'github', 'gitlab', 'bitbucket', 'git workflow', 'version control'}
        aliases['excel'] = {'microsoft excel', 'ms excel', 'excel vba', 'excel macros', 'spreadsheet'}
        aliases['tableau'] = {'tableau desktop', 'tableau server', 'tableau prep', 'data visualization'}
        
        # Add aliases to known skills mapping
        skill_to_aliases = {}
        for skill in self.known_skills:
            skill_lower = skill.lower()
            # Check if skill matches any alias
            for main_skill, alias_set in aliases.items():
                if skill_lower == main_skill or skill_lower in alias_set:
                    skill_to_aliases[skill] = aliases[main_skill]
                    break
        
        return skill_to_aliases
    
    def _normalize_skills(self):
        """Normalize skill names and create variations"""
        self.skill_variations = {}
        for skill in self.known_skills:
            variations = {skill}
            skill_lower = skill.lower()
            
            # Add common variations
            variations.add(skill_lower.replace(' ', '-'))
            variations.add(skill_lower.replace(' ', '_'))
            variations.add(skill_lower.replace('-', ' '))
            variations.add(skill_lower.replace('_', ' '))
            
            # Handle plural forms
            if skill_lower.endswith('s'):
                variations.add(skill_lower[:-1])
            else:
                variations.add(skill_lower + 's')
            
            self.skill_variations[skill] = variations
    
    def extract_from_pdf(self, pdf_file) -> List[str]:
        """Extract skills from PDF file with enhanced extraction"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 is not installed. Install it with: pip install PyPDF2")
        
        try:
            text = self._read_pdf(pdf_file)
            return self.extract_from_text(text)
        except Exception as e:
            print(f"Error extracting from PDF: {e}")
            return []
    
    def extract_from_docx(self, docx_file) -> List[str]:
        """Extract skills from DOCX file with enhanced extraction"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is not installed. Install it with: pip install python-docx")
        
        try:
            text = self._read_docx(docx_file)
            return self.extract_from_text(text)
        except Exception as e:
            print(f"Error extracting from DOCX: {e}")
            return []
    
    def extract_from_text(self, text: str, return_confidence: bool = False) -> List[str]:
        """
        Enhanced skill extraction from text using multiple strategies
        
        Args:
            text: Input text to extract skills from
            return_confidence: If True, returns list of tuples (skill, confidence_score)
        
        Returns:
            List of skills or list of (skill, confidence) tuples
        """
        if not text or len(text.strip()) < 10:
            return []
        
        # Try LLM extraction first if enabled
        if self.use_llm:
            try:
                llm_skills = self._extract_with_llm(text)
                if llm_skills:
                    # Use LLM results as primary, then enhance with pattern matching
                    skill_confidence = defaultdict(float)
                    # LLM results get high confidence
                    for skill in llm_skills:
                        skill_confidence[skill] = 0.95
                    
                    # Enhance with pattern matching for additional skills
                    pattern_skills = self._extract_with_patterns(text)
                    for skill in pattern_skills:
                        if skill not in skill_confidence:
                            skill_confidence[skill] = 0.7
                        else:
                            # Boost confidence if pattern matching confirms LLM result
                            skill_confidence[skill] = min(1.0, skill_confidence[skill] + 0.1)
                    
                    if return_confidence:
                        return sorted(skill_confidence.items(), key=lambda x: x[1], reverse=True)
                    else:
                        return sorted([s for s in skill_confidence.keys() if skill_confidence[s] >= 0.5])
            except Exception as e:
                print(f"⚠️ LLM extraction failed: {e}. Falling back to pattern matching.")
                # Fall through to pattern matching
        
        # Pattern-based extraction (fallback or primary method)
        return self._extract_with_patterns(text, return_confidence)
    
    def _extract_with_patterns(self, text: str, return_confidence: bool = False) -> List[str]:
        """Extract skills using pattern matching strategies"""
        # Preprocess text
        text_processed = self._preprocess_text(text)
        text_lower = text_processed.lower()
        
        # Track skills with confidence scores
        skill_confidence = defaultdict(float)
        skill_sources = defaultdict(list)
        
        # Strategy 1: Extract from skills sections (highest confidence)
        skills_from_sections = self._extract_from_skills_sections(text_processed)
        for skill in skills_from_sections:
            skill_confidence[skill] += 1.0
            skill_sources[skill].append('skills_section')
        
        # Strategy 2: Direct word boundary matching (high confidence)
        direct_matches = self._direct_matching(text_lower)
        for skill in direct_matches:
            skill_confidence[skill] += 0.9
            skill_sources[skill].append('direct_match')
        
        # Strategy 3: Pattern-based extraction (medium confidence)
        pattern_matches = self._pattern_based_extraction(text_lower)
        for skill in pattern_matches:
            skill_confidence[skill] += 0.7
            skill_sources[skill].append('pattern_match')
        
        # Strategy 4: Context-aware extraction (medium confidence)
        context_matches = self._context_aware_extraction(text_lower)
        for skill in context_matches:
            skill_confidence[skill] += 0.6
            skill_sources[skill].append('context_match')
        
        # Strategy 5: Abbreviation and alias matching (lower confidence)
        alias_matches = self._alias_matching(text_lower)
        for skill in alias_matches:
            skill_confidence[skill] += 0.5
            skill_sources[skill].append('alias_match')
        
        # Normalize confidence scores (0-1 range)
        if skill_confidence:
            max_confidence = max(skill_confidence.values())
            for skill in skill_confidence:
                skill_confidence[skill] = min(1.0, skill_confidence[skill] / max_confidence)
        
        if return_confidence:
            # Return sorted by confidence
            return sorted(skill_confidence.items(), key=lambda x: x[1], reverse=True)
        else:
            # Filter by minimum confidence threshold
            min_confidence = 0.3
            high_confidence_skills = [skill for skill, conf in skill_confidence.items() if conf >= min_confidence]
            return sorted(high_confidence_skills)
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better extraction"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-\+\#\.\(\)\/]', ' ', text)
        
        # Fix common encoding issues
        text = text.replace('\xa0', ' ')  # Non-breaking space
        text = text.replace('\u2009', ' ')  # Thin space
        text = text.replace('\u2026', '...')  # Ellipsis
        
        # Normalize bullet points
        text = re.sub(r'[•·▪▫\-\*\+]\s*', ' ', text)
        
        return text
    
    def _extract_from_skills_sections(self, text: str) -> Set[str]:
        """Extract skills from dedicated skills sections"""
        found = set()
        
        # Common section headers
        section_patterns = [
            r'(?:technical\s+)?skills\s*[:]\s*(.*?)(?:\n\n|\n[A-Z]|\Z)',
            r'(?:core\s+)?competencies?\s*[:]\s*(.*?)(?:\n\n|\n[A-Z]|\Z)',
            r'technologies?\s*[:]\s*(.*?)(?:\n\n|\n[A-Z]|\Z)',
            r'(?:programming\s+)?languages?\s*[:]\s*(.*?)(?:\n\n|\n[A-Z]|\Z)',
            r'tools?\s+and\s+technologies?\s*[:]\s*(.*?)(?:\n\n|\n[A-Z]|\Z)',
            r'expertise\s*[:]\s*(.*?)(?:\n\n|\n[A-Z]|\Z)',
        ]
        
        text_lower = text.lower()
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section_text = match.group(1)
                # Extract skills from this section
                section_skills = self._extract_from_section(section_text)
                found.update(section_skills)
        
        return found
    
    def _extract_from_section(self, section_text: str) -> Set[str]:
        """Extract skills from a specific section"""
        found = set()
        section_lower = section_text.lower()
        
        # Split by common separators
        parts = re.split(r'[,;•·\|\n\r]+', section_text)
        
        for part in parts:
            part = part.strip()
            if len(part) < 2:
                continue
            
            part_lower = part.lower()
            
            # Check against known skills
            for skill in self.known_skills:
                # Exact match
                if part_lower == skill:
                    found.add(skill)
                    continue
                
                # Contains skill
                if skill in part_lower:
                    found.add(skill)
                    continue
                
                # Check variations
                if skill in self.skill_variations:
                    for variation in self.skill_variations[skill]:
                        if variation in part_lower or part_lower in variation:
                            found.add(skill)
                            break
        
        return found
    
    def _direct_matching(self, text: str) -> Set[str]:
        """Direct word boundary matching with variations"""
        found = set()
        
        for skill in self.known_skills:
            # Try all variations
            variations = self.skill_variations.get(skill, {skill})
            
            for variation in variations:
                # Word boundary matching
                pattern = r'\b' + re.escape(variation) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    found.add(skill)
                    break
                
                # Also try without word boundaries for compound skills
                if variation in text:
                    # Check if it's not part of a larger word
                    pattern_check = r'(?:^|[^\w])' + re.escape(variation) + r'(?:[^\w]|$)'
                    if re.search(pattern_check, text, re.IGNORECASE):
                        found.add(skill)
                        break
        
        return found
    
    def _pattern_based_extraction(self, text: str) -> Set[str]:
        """Extract skills using pattern matching"""
        found = set()
        
        # Enhanced patterns for skill mentions
        skill_patterns = [
            # "Experienced in X, Y, Z"
            r'(?:experienced|proficient|skilled|expert|advanced|knowledgeable)\s+(?:in|with|at)?\s*:?\s*([^\.\n]{10,200})',
            # "Skills: X, Y, Z"
            r'(?:skills?|technologies?|tools?|languages?|frameworks?)\s*:?\s*([^\.\n]{10,200})',
            # "Worked with X, Y, Z"
            r'(?:worked|experience|using|utilizing|implementing)\s+(?:with|in)?\s*([^\.\n]{10,200})',
            # "Familiar with X, Y, Z"
            r'(?:familiar|comfortable|good)\s+(?:with|in)?\s*([^\.\n]{10,200})',
            # "X, Y, Z expertise"
            r'([A-Z][^\.\n]{5,100})\s+(?:expertise|experience|proficiency|skills)',
            # Bullet points with skills
            r'[-•·]\s*([A-Z][^\.\n]{3,50})(?:\s*[,-]\s*[A-Z][^\.\n]{3,50})*',
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                match_text = match.group(1)
                # Extract skills from matched text
                extracted = self._extract_from_section(match_text)
                found.update(extracted)
        
        return found
    
    def _context_aware_extraction(self, text: str) -> Set[str]:
        """Extract skills based on context keywords"""
        found = set()
        
        # Context keywords that indicate skill mentions
        context_keywords = [
            'developed', 'built', 'created', 'designed', 'implemented',
            'programming', 'coding', 'development', 'framework', 'library',
            'technology', 'platform', 'tool', 'software', 'system'
        ]
        
        # Look for skills near context keywords
        for keyword in context_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\s+[^\s]{1,30}'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                context_text = match.group(0)
                # Extract potential skills from context
                for skill in self.known_skills:
                    if skill in context_text.lower():
                        found.add(skill)
        
        return found
    
    def _alias_matching(self, text: str) -> Set[str]:
        """Match skills using aliases and abbreviations"""
        found = set()
        
        # Common abbreviations mapping
        abbreviations = {
            'ml': 'machine learning',
            'ai': 'machine learning',  # Often used interchangeably
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'k8s': 'kubernetes',
            'aws': 'aws',
            'gcp': 'google cloud platform',
            'api': 'rest api',
            'db': 'database',
        }
        
        # Check for abbreviations
        for abbrev, full_skill in abbreviations.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                # Find matching known skill
                for skill in self.known_skills:
                    if full_skill in skill or skill in full_skill:
                        found.add(skill)
        
        # Check skill aliases
        for skill, aliases in self.skill_aliases.items():
            for alias in aliases:
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    if skill in self.known_skills:
                        found.add(skill)
        
        return found
    
    def _extract_with_llm(self, text: str) -> List[str]:
        """
        Extract skills using LLM (OpenAI API)
        
        Args:
            text: Input text to extract skills from
        
        Returns:
            List of extracted skills that match known_skills
        """
        if not OPENAI_AVAILABLE:
            return []
        
        try:
            # Truncate text if too long (OpenAI has token limits)
            max_chars = 8000  # Leave room for prompt
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            # Create prompt
            skills_list = sorted(list(self.known_skills))[:200]  # Limit to avoid token limits
            prompt = f"""Extract technical skills from the following text. Only return skills that are in the provided list of known skills.

Known skills list:
{', '.join(skills_list[:100])}

Text to analyze:
{text}

Instructions:
1. Identify all technical skills mentioned in the text
2. Only return skills that match (exactly or closely) items from the known skills list
3. Return skills as a comma-separated list
4. Use lowercase and match the format from the known skills list
5. If a skill has multiple words, preserve the exact format from the known skills list

Return only the skills, comma-separated, nothing else:"""

            # Try new OpenAI client first (v1.0+)
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use cheaper model
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts technical skills from text."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                result = response.choices[0].message.content.strip()
            except (ImportError, AttributeError):
                # Fallback to older OpenAI API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts technical skills from text."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                result = response.choices[0].message.content.strip()
            
            # Parse response
            extracted = []
            if result:
                # Split by comma and clean
                skills_raw = [s.strip().lower() for s in result.split(',')]
                # Match against known skills
                for skill_raw in skills_raw:
                    # Direct match
                    if skill_raw in self.known_skills:
                        extracted.append(skill_raw)
                    else:
                        # Fuzzy match - check if it's similar to any known skill
                        for known_skill in self.known_skills:
                            if skill_raw in known_skill or known_skill in skill_raw:
                                extracted.append(known_skill)
                                break
                            # Check variations
                            if known_skill in self.skill_variations:
                                for variation in self.skill_variations[known_skill]:
                                    if skill_raw == variation or skill_raw in variation:
                                        extracted.append(known_skill)
                                        break
            
            return list(set(extracted))  # Remove duplicates
            
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return []
    
    def _read_pdf(self, pdf_file) -> str:
        """Enhanced PDF reading with better text extraction"""
        try:
            # Reset file pointer
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
            text_parts = []
            
            # Extract from all pages
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    print(f"Warning: Could not extract text from page {page_num}: {e}")
                    continue
            
            # Also try extracting from annotations/form fields
            if hasattr(pdf_reader, 'pages') and len(pdf_reader.pages) > 0:
                try:
                    # Some PDFs have text in different layers
                    for page in pdf_reader.pages:
                        if hasattr(page, 'get_contents'):
                            try:
                                contents = page.get_contents()
                                if contents:
                                    text_parts.append(str(contents))
                            except:
                                pass
                except:
                    pass
            
            full_text = "\n".join(text_parts)
            
            # Clean up PDF extraction artifacts
            full_text = re.sub(r'\x0c', '\n', full_text)  # Form feed
            full_text = re.sub(r'\s+', ' ', full_text)  # Normalize whitespace
            
            return full_text
            
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def _read_docx(self, docx_file) -> str:
        """Enhanced DOCX reading with table and formatting support"""
        try:
            # Reset file pointer
            if hasattr(docx_file, 'seek'):
                docx_file.seek(0)
            
            doc = docx.Document(BytesIO(docx_file.read()))
            text_parts = []
            
            # Extract from paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            # Extract from tables (often contain skills in CVs)
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(" | ".join(row_text))
            
            # Extract from headers/footers if available
            try:
                for section in doc.sections:
                    if section.header:
                        text_parts.append(section.header.text)
                    if section.footer:
                        text_parts.append(section.footer.text)
            except:
                pass
            
            full_text = "\n".join(text_parts)
            
            # Clean up
            full_text = re.sub(r'\s+', ' ', full_text)
            
            return full_text
            
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
