import re
import PyPDF2
import docx
import io
import streamlit as st
from config.settings import CONFIDENCE_THRESHOLDS
import json
# Import LLMManager lazily inside functions to avoid circular imports during app startup

def generate_motivation_message(resume_analysis_results):
    """Generate personalized motivation based on resume analysis"""
    consistency_score = resume_analysis_results.get('consistency_score', 0)
    strengths = resume_analysis_results.get('strengths', [])
    
    # Craft personalized motivation
    if consistency_score >= 0.8 and strengths:
        message = f"Your experience in {strengths[0]} stands out. Let's showcase your expertise!"
    elif consistency_score >= 0.6:
        message = "Your background shows promise. This assessment will highlight your potential."
    else:
        message = "Every question is an opportunity to demonstrate your capabilities!"
    
    return message

def extract_text_from_resume(uploaded_file):
    """Extract text from PDF or DOCX resume with comprehensive error handling"""
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                for page in pdf_reader.pages:
                    try:
                        text += page.extract_text()
                    except Exception as page_err:
                        print(f"Warning: Failed to extract text from PDF page: {page_err}")
                        continue
            except Exception as pdf_err:
                raise ValueError(f"PDF processing error: {str(pdf_err)}")
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            try:
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                for paragraph in doc.paragraphs:
                    try:
                        text += paragraph.text + "\n"
                    except Exception as para_err:
                        print(f"Warning: Failed to extract text from paragraph: {para_err}")
                        continue
            except Exception as docx_err:
                raise ValueError(f"DOCX processing error: {str(docx_err)}")
        else:
            raise ValueError(f"Unsupported file format: {uploaded_file.type}")
        
        if not text or not text.strip():
            raise ValueError("Resume file is empty or contains no extractable text")
        
        return text
    except Exception as e:
        print(f"Error processing resume: {str(e)}")
        if 'st' in globals():
            st.error(f"Resume extraction failed: {str(e)}")
        return ""

        
def analyze_resume_consistency(resume_text, candidate_info):
    """
    Analyze resume for consistency with provided information
    Returns: (consistency_score, findings)
    """
    findings = []
    consistency_score = 1.0  # Start with perfect score
    
    # Check years of experience
    experience_patterns = [
        r'(\d+)[\+]?\s*(?:years?|yrs?).+?experience',
        r'experience.+?(\d+)[\+]?\s*(?:years?|yrs?)',
        r'(\d{4})\s*-\s*(?:present|current|now|2024)',  # Add more year patterns
    ]
    
    claimed_years = candidate_info.get("Years of Experience", 0)
    years_found = []
    
    # Extract years from dates
    for pattern in experience_patterns:
        matches = re.finditer(pattern, resume_text.lower())
        for match in matches:
            if match.group(1).isdigit():
                if len(match.group(1)) == 4:  # It's a year
                    years = 2024 - int(match.group(1))
                    years_found.append(years)
                else:
                    years_found.append(int(match.group(1)))
    
    if years_found:
        max_years = max(years_found)
        if abs(max_years - claimed_years) > 2:
            consistency_score += CONFIDENCE_THRESHOLDS['experience_mismatch_penalty']
            findings.append(f"Experience discrepancy: Claimed {claimed_years} years, Resume suggests {max_years} years")
    
    # Check skills match
    claimed_skills = set(skill.lower() for skill in candidate_info.get("Tech Stack", []))
    found_skills = set()
    
    # Build comprehensive tech stack regex
    tech_keywords = {
        'languages': r'python|java|javascript|c\+\+|ruby|php|swift|kotlin|go|rust',
        'frameworks': r'django|flask|spring|react|angular|vue|express|rails|laravel',
        'databases': r'sql|mysql|postgresql|mongodb|redis|elasticsearch|cassandra',
        'tools': r'git|docker|kubernetes|jenkins|aws|azure|gcp|terraform|ansible'
    }
    
    for category, pattern in tech_keywords.items():
        matches = re.finditer(pattern, resume_text.lower())
        for match in matches:
            found_skills.add(match.group())
    
    # Compare skills
    missing_skills = claimed_skills - found_skills
    if missing_skills:
        penalty = len(missing_skills) * CONFIDENCE_THRESHOLDS['skill_mismatch_penalty']
        consistency_score += penalty
        findings.append(f"Skills mentioned but not found in resume: {', '.join(missing_skills)}")
    
    # Check position alignment
    desired_position = candidate_info.get("Desired Position", "").lower()
    position_words = set(desired_position.split())
    position_match = any(word in resume_text.lower() for word in position_words if len(word) > 3)
    
    if not position_match:
        consistency_score += CONFIDENCE_THRESHOLDS['resume_mismatch_penalty']
        findings.append("Desired position not aligned with resume content")
    else:
        consistency_score += CONFIDENCE_THRESHOLDS['resume_match_bonus']
    
    # Normalize final score
    consistency_score = max(0.0, min(consistency_score, 1.0))
    
    return consistency_score, findings

def parse_resume_with_llm(resume_text):
    """
    Extract structured information from resume text using LLM
    Returns a dictionary with candidate details, or None if parsing fails
    """
    try:
        # Import LLMManager here to avoid circular import issues during module import
        from models.llm_manager import LLMManager
        
        try:
            llm = LLMManager.get_llm('conversation', temperature=0.1)
        except Exception as llm_err:
            print(f"Failed to initialize LLM: {str(llm_err)}")
            return None
        
        # If we are using a local stub because no API key is present, avoid attempting
        # to parse JSON via the LLM (it will return a stub text and lead to parse errors).
        if getattr(llm, '_backend', '').startswith('Local Stub') or not getattr(llm, '_key_format_valid', True):
            print("LLM backend is a local stub or API key invalid; skipping LLM-based parsing.")
            return None
        
        prompt = f"""
        You are an expert HR assistant. Extract the following candidate information from the resume text below.
        Return ONLY a valid JSON object with these exact keys:
        - "Full Name": string (or empty string if not found)
        - "Email": string (or empty string if not found)
        - "Phone": string (or empty string if not found)
        - "Years of Experience": integer (0 if not found)
        - "Desired Position": string (infer from experience or objective, default to "Software Engineer")
        - "Location": string (or empty string if not found)
        - "Tech Stack": list of strings (extract all technical skills, languages, frameworks)

        Resume Text:
        {resume_text[:4000]}  # Truncate to avoid context limit issues
        
        JSON Response:
        """
        
        try:
            response = llm.invoke(prompt)
            if not response:
                print("LLM returned empty response")
                return None
            
            response_content = getattr(response, 'content', str(response))
            if not response_content:
                print("LLM response has no content")
                return None
        except Exception as invoke_err:
            print(f"Error invoking LLM: {str(invoke_err)}")
            return None
        
        # Clean response to ensure valid JSON
        json_str = response_content.strip()
        
        # Extract JSON from markdown code blocks if present
        try:
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
        except (IndexError, ValueError) as parse_err:
            print(f"Warning: Could not extract JSON from code blocks: {parse_err}")
        
        # Attempt to parse JSON
        try:
            data = json.loads(json_str)
            # Validate required keys exist (with defaults)
            required_fields = {
                "Full Name": "",
                "Email": "",
                "Phone": "",
                "Years of Experience": 0,
                "Desired Position": "Software Engineer",
                "Location": "",
                "Tech Stack": []
            }
            for key, default in required_fields.items():
                if key not in data:
                    data[key] = default
            return data
        except json.JSONDecodeError as json_err:
            print(f"JSON parsing error: {str(json_err)}")
            print(f"Failed to parse: {json_str[:200]}")
            return None
        
    except Exception as e:
        print(f"Unexpected error parsing resume with LLM: {str(e)}")
        return None