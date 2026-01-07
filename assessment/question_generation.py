"""Question Generation Module - TalentScout Hiring Assistant

This module handles dynamic technical question generation based on candidate's
tech stack, experience level, and previous responses.
"""

import streamlit as st
import re

# Explicit question templates for common tech stacks
TECH_STACK_QUESTIONS = {
    "python": [
        "What is the difference between a list and a tuple in Python?",
        "Explain how Python's garbage collection works and what reference counting means.",
        "How would you handle exceptions when reading from multiple files in a Python application?",
        "Describe the Global Interpreter Lock (GIL) and its impact on multi-threaded Python programs.",
        "What are metaclasses in Python and when would you use them?"
    ],
    "javascript": [
        "What is the difference between let, const, and var in JavaScript?",
        "Explain event bubbling and event capturing in the DOM.",
        "How would you implement debouncing for a search input field?",
        "Describe the JavaScript event loop and how asynchronous code execution works.",
        "What are JavaScript Proxies and Reflect API, and what are their use cases?"
    ],
    "react": [
        "What is the virtual DOM and why does React use it?",
        "Explain the difference between controlled and uncontrolled components.",
        "How would you optimize a React component that re-renders too frequently?",
        "Describe the useEffect hook and its dependency array behavior.",
        "What are React Server Components and how do they differ from traditional components?"
    ],
    "django": [
        "Explain the MVT (Model-View-Template) pattern in Django.",
        "How does Django's ORM handle database queries and what is lazy evaluation?",
        "How would you implement user authentication and authorization in a Django application?",
        "Describe Django middleware and provide an example use case.",
        "How would you optimize Django application performance for high-traffic scenarios?"
    ],
    "sql": [
        "What is the difference between INNER JOIN and LEFT JOIN?",
        "Explain database normalization and the first three normal forms.",
        "How would you design a database schema for an e-commerce application?",
        "What are database indexes and how do they improve query performance?",
        "Describe ACID properties and how they ensure database transaction reliability."
    ],
    "git": [
        "What is the difference between git pull and git fetch?",
        "Explain the Git branching strategy you would use for a team project.",
        "How would you resolve a merge conflict in Git?"
    ],
    "docker": [
        "What is the difference between a Docker image and a Docker container?",
        "Explain how Docker networking works and the different network types.",
        "How would you optimize a Dockerfile for production deployment?"
    ],
    "aws": [
        "What is the difference between IaaS, PaaS, and SaaS?",
        "Explain how you would deploy a web application to AWS.",
        "Describe auto-scaling and load balancing in AWS.",
        "How would you design a highly available, fault-tolerant architecture on AWS?"
    ]
}

def get_explicit_questions_for_tech(tech_stack):
    """Get explicit questions for the given tech stack"""
    questions = []
    tech_stack_lower = [tech.lower().strip() for tech in tech_stack]
    
    for tech in tech_stack_lower:
        # Check for exact matches or partial matches
        for key, tech_questions in TECH_STACK_QUESTIONS.items():
            if key in tech or tech in key:
                questions.extend(tech_questions)
    
    return questions

def detect_exit_keywords(text):
    """Detect if user wants to exit the assessment"""
    exit_keywords = ['exit', 'quit', 'stop', 'end assessment', 'end']
    text_lower = text.lower().strip()
    
    for keyword in exit_keywords:
        if keyword in text_lower:
            return True
    return False

# Function to generate technical questions
def generate_technical_questions(tech_stack, conversation):
    # First, try to get explicit questions
    if isinstance(tech_stack, str):
        tech_list = [t.strip() for t in tech_stack.split(',')]
    else:
        tech_list = tech_stack
    
    explicit_questions = get_explicit_questions_for_tech(tech_list)
    
    # If we have explicit questions, use them
    if explicit_questions:
        return explicit_questions[:5]
    
    # Otherwise, generate using LLM
    prompt = f"""
    Based on the tech stack: {tech_stack}, generate 5 questions with increasing difficulty:

    1. Start with a basic concept/definition question (easy, short answer)
    2. Progress to fundamentals application (moderate, brief explanation)
    3. Add a practical scenario (moderate, focused solution)
    4. Include problem-solving (challenging but specific)
    5. End with advanced concepts (if needed based on previous answers)

    Rules:
    - First 2 questions should be answerable in 1-2 sentences
    - Questions 3-4 should need 3-4 sentences max
    - Keep questions focused and specific
    - Avoid asking for code implementations
    - Use this format: "Question N: [The question text]"

    Example progression:
    Question 1: What is [basic concept] in {tech_stack}?
    Question 2: How does [fundamental feature] work in {tech_stack}?
    Question 3: In a simple web app, how would you handle [specific scenario]?
    Question 4: What approach would you take to solve [specific problem]?
    Question 5: Explain the trade-offs between [advanced concept A] and [advanced concept B].

    Generate questions that are concise and clear.
    """
   
    try:
        response_msg = conversation.invoke({"input": prompt, "history": []})
        response = response_msg.content
        
        questions = []
        for line in response.splitlines():
            if line.strip().startswith('Question'):
                questions.append(line.strip())
        
        return questions[:5]  # Ensure we only return 5 questions
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return ["Error generating questions. Please try again."]


def generate_focused_question(tech_stack, focus_areas, previous_questions, conversation):
    """Generate a new question based on focus areas and previous questions"""
    focus_areas_str = ", ".join(focus_areas) if focus_areas else "general technical knowledge"
    
    prompt = f"""
    Based on the candidate's previous responses, generate ONE focused technical question.
    Tech Stack: {tech_stack}
    Focus Areas Needed: {focus_areas_str}
    
    Previous Questions Asked:
    {previous_questions}
    
    Generate a NEW question that:
    1. Probes deeper into the identified focus areas
    2. Is different from previous questions
    3. Helps assess technical depth and problem-solving
    
    Return ONLY the question text, no additional formatting or commentary.
    """
    
    try:
        new_question = conversation.invoke({"input": prompt, "history": []}).content.strip()
        # Verify it's not too similar to previous questions
        if any(similar_questions(new_question, prev_q) for prev_q in previous_questions):
            # Try one more time with explicit differentiation
            prompt += "\nIMPORTANT: Question must be substantially different from previous questions!"
            new_question = conversation.invoke({"input": prompt, "history": []}).content.strip()
        
        return new_question
    except Exception as e:
        return f"Error generating question: {str(e)}"

def similar_questions(q1, q2):
    """Basic similarity check between questions"""
    q1_words = set(q1.lower().split())
    q2_words = set(q2.lower().split())
    common_words = q1_words.intersection(q2_words)
    similarity = len(common_words) / max(len(q1_words), len(q2_words))
    return similarity > 0.7        
