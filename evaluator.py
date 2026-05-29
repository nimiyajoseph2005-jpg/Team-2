import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use a model that supports system instructions and JSON structure for better results
# Using gemini-2.5-flash-lite as requested for higher limits
model = genai.GenerativeModel('gemini-2.5-flash-lite')

def evaluate_resume(resume_text, job_title, skills, experience, qualifications, mock_mode=False):
    """
    Evaluate a resume against job requirements using Gemini API.
    Returns a dictionary with Name, Score, Matched Skills, and Experience Verdict.
    """
    if mock_mode:
        time.sleep(0.5) # Simulate processing
        import random
        # Extract a fake name from the first few words if possible, else "Mock Candidate"
        words = resume_text.split()
        name = " ".join(words[:2]) if len(words) >= 2 else "Mock Candidate"
        # Dummy skills
        req_skills = [s.strip() for s in skills.split(',')] if skills else ["Python", "SQL"]
        matched_skills = random.sample(req_skills, k=min(len(req_skills), random.randint(1, max(1, len(req_skills)))))
        score = random.randint(40, 95)
        return {
            "name": name,
            "score": score,
            "matched_skills": matched_skills,
            "experience_verdict": f"[MOCK MODE] This is a dummy verdict. The candidate has some experience matching {experience}."
        }
    prompt = f"""
    You are an expert HR AI assistant. Your task is to evaluate a candidate's resume against a set of job requirements.
    
    Job Requirements:
    - Job Title: {job_title}
    - Required Skills: {skills}
    - Experience Level: {experience}
    - Qualifications: {qualifications}
    
    Resume Text:
    ---
    {resume_text}
    ---
    
    Evaluate the resume and return a JSON object with the following structure exactly (no markdown formatting, just raw JSON):
    {{
        "name": "Candidate Name (extract from resume, or 'Unknown')",
        "score": <An integer from 0 to 100 based on how well the candidate matches the requirements>,
        "matched_skills": ["Skill 1", "Skill 2"],
        "experience_verdict": "A brief 1-2 sentence verdict on their experience and qualifications match."
    }}
    """
    
    max_retries = 5
    retry_delay = 15
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(retry_delay)
                
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            result = json.loads(response.text)
            # Ensure default values in case of missing keys
            result.setdefault("name", "Unknown")
            result.setdefault("score", 0)
            result.setdefault("matched_skills", [])
            result.setdefault("experience_verdict", "No verdict available.")
            return result
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                continue
            
            if attempt == max_retries - 1:
                print(f"Error evaluating resume after retries: {e}")
                return {
                    "name": "Error Processing",
                    "score": 0,
                    "matched_skills": [],
                    "experience_verdict": f"Error: {str(e)}"
                }
