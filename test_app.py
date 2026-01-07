#!/usr/bin/env python3
"""Quick test of the TalentScout application"""

import sys
import os

# Set up path
sys.path.insert(0, '/workspaces/TalentScout-Hiring-Assistant')
os.chdir('/workspaces/TalentScout-Hiring-Assistant')

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from config.settings import CONFIDENCE_THRESHOLDS, CONVERSATION_MEMORY_LENGTH
        print("✓ config.settings")
    except Exception as e:
        print(f"✗ config.settings: {e}")
        return False

    try:
        from utils.validators import validate_email, validate_phone, validate_tech_stack
        print("✓ utils.validators")
    except Exception as e:
        print(f"✗ utils.validators: {e}")
        return False

    try:
        from utils.resume_processing import extract_text_from_resume
        print("✓ utils.resume_processing")
    except Exception as e:
        print(f"✗ utils.resume_processing: {e}")
        return False

    try:
        from utils.i18n import get_text, get_available_languages
        print("✓ utils.i18n")
    except Exception as e:
        print(f"✗ utils.i18n: {e}")
        return False

    try:
        from utils.sentiment_analyzer import analyze_sentiment, get_sentiment_feedback
        print("✓ utils.sentiment_analyzer")
    except Exception as e:
        print(f"✗ utils.sentiment_analyzer: {e}")
        return False

    try:
        from utils.ui_themes import get_custom_css, get_available_themes
        print("✓ utils.ui_themes")
    except Exception as e:
        print(f"✗ utils.ui_themes: {e}")
        return False

    try:
        # Suppress streamlit warnings by importing quietly
        import streamlit as st
        import streamlit_shadcn_ui as ui
        print("✓ streamlit & streamlit_shadcn_ui")
    except Exception as e:
        print(f"✗ streamlit modules: {e}")
        return False

    try:
        from components.sidebar import render_sidebar
        print("✓ components.sidebar")
    except Exception as e:
        print(f"✗ components.sidebar: {e}")
        return False

    try:
        from components.progress import create_progress_container, update_assessment_progress
        print("✓ components.progress")
    except Exception as e:
        print(f"✗ components.progress: {e}")
        return False

    try:
        from assessment.question_generation import (
            generate_technical_questions,
            generate_focused_question,
            similar_questions,
            detect_exit_keywords
        )
        print("✓ assessment.question_generation")
    except Exception as e:
        print(f"✗ assessment.question_generation: {e}")
        return False

    try:
        from assessment.evaluation import (
            evaluate_answer_with_llm,
            fallback_evaluation,
            generate_detailed_feedback_with_llm,
            generate_final_recommendation_with_llm,
            generate_fallback_recommendation,
            assess_confidence_level,
            determine_focus_areas,
            extract_technical_terms
        )
        print("✓ assessment.evaluation")
    except Exception as e:
        print(f"✗ assessment.evaluation: {e}")
        return False

    try:
        from reporting.report_generator import generate_report
        print("✓ reporting.report_generator")
    except Exception as e:
        print(f"✗ reporting.report_generator: {e}")
        return False

    try:
        from models.llm_manager import determine_optimal_persona, get_persona_prompt, LLMManager
        print("✓ models.llm_manager")
    except Exception as e:
        print(f"✗ models.llm_manager: {e}")
        return False

    return True

def test_basic_functionality():
    """Test basic functionality of key modules"""
    print("\nTesting basic functionality...")

    try:
        from utils.validators import validate_email
        assert validate_email("test@example.com") == True
        assert validate_email("invalid-email") == False
        print("✓ Email validation works")
    except Exception as e:
        print(f"✗ Email validation: {e}")
        return False

    try:
        from utils.validators import validate_phone
        assert validate_phone("+1-555-0123") == True
        assert validate_phone("(555) 123-4567") == True
        assert validate_phone("invalid") == False
        print("✓ Phone validation works")
    except Exception as e:
        print(f"✗ Phone validation: {e}")
        return False

    try:
        from utils.validators import validate_tech_stack
        assert validate_tech_stack("Python, JavaScript") == True
        assert validate_tech_stack("") == False
        print("✓ Tech stack validation works")
    except Exception as e:
        print(f"✗ Tech stack validation: {e}")
        return False

    try:
        from assessment.question_generation import detect_exit_keywords
        assert detect_exit_keywords("exit") == True
        assert detect_exit_keywords("Can you answer this?") == False
        print("✓ Exit keyword detection works")
    except Exception as e:
        print(f"✗ Exit keyword detection: {e}")
        return False

    try:
        from assessment.question_generation import similar_questions
        result = similar_questions("What is Python?", "What is Python programming?")
        print(f"✓ Similar questions comparison works (similarity: {result})")
    except Exception as e:
        print(f"✗ Similar questions: {e}")
        return False

    return True

if __name__ == "__main__":
    print("=" * 50)
    print("TalentScout Application Test Suite")
    print("=" * 50)
    
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n✗ Import tests failed!")
        sys.exit(1)
    
    print("\n✓ All imports successful!")
    
    functionality_ok = test_basic_functionality()
    
    if not functionality_ok:
        print("\n✗ Functionality tests failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    print("=" * 50)
    print("\nThe application is ready to run. Use:")
    print("  streamlit run version_3.py")
