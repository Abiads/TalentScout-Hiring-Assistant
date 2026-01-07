"""TalentScout Hiring Assistant - AI-Powered Technical Assessment Platform

Author: Abhay Gupta
GitHub: https://github.com/Abs6187
LinkedIn: linkedin.com/in/abhay-gupta-197b17264
Linktree: https://linktr.ee/Abhay_Gupta_6187

Created: January 2026
License: MIT
"""

import streamlit as st
import streamlit_shadcn_ui as ui
from config.settings import CONFIDENCE_THRESHOLDS, CONVERSATION_MEMORY_LENGTH
from utils.validators import validate_email, validate_phone, validate_tech_stack
from utils.resume_processing import extract_text_from_resume, analyze_resume_consistency, parse_resume_with_llm
from utils.i18n import get_text, get_available_languages
from utils.sentiment_analyzer import analyze_sentiment, get_sentiment_feedback
from utils.ui_themes import get_custom_css, get_available_themes
from components.sidebar import render_sidebar
from components.progress import create_progress_container, update_assessment_progress
from assessment.question_generation import generate_technical_questions, generate_focused_question, similar_questions
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
from reporting.report_generator import generate_report
from models.llm_manager import determine_optimal_persona, get_persona_prompt, LLMManager
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from datetime import datetime
import json
import re


# Initialize Streamlit page configuration
st.set_page_config(
    page_title='TalentScout Hiring Assistant',
    page_icon='📋',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Apply custom theme colors
st.markdown("""
<style>
    :root {
        --primary-color: #3b82f6;
        --secondary-color: #1e40af;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)



# Load environment variables securely
# Do not hardcode API keys — allow user to paste one via the advanced sidebar
CONVERSATION_MEMORY_LENGTH = 10
# Initialize session state variables
def initialize_session_state():
    session_vars = {
        'chat_history': [],
        'total_messages': 0,
        'start_time': None,
        'candidate_info': {},
        'current_question': None,
        'assessment_completed': False,
        'answers': {},
        'evaluation_scores': {},
        'recommendation': None,
        'technical_questions': [],
        'current_question_index': 0,
        'current_answer': '',
        'questions_asked': 0,
        'language': 'en',  # Default language
        'theme': 'professional',  # Default theme
        'sentiment_scores': {},  # Store sentiment analysis results
        'groq_api_key': '',
        'allow_local_models': False,
    }
    
    for var, default in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default


def main():
    """Main application function with comprehensive error handling"""
    initialize_session_state()
    
    # Initialize LLM with error handling
    try:
        llm = LLMManager.get_llm(
            'conversation', 
            api_key=st.session_state.get('groq_api_key') or None, 
            allow_local_models=st.session_state.get('allow_local_models', False)
        )
    except Exception as e:
        st.error(f"⚠️ Failed to initialize AI components: {str(e)}")
        st.info("💡 Try adding a Groq API key in the Advanced Options section in the left sidebar.")
        st.stop()
    # Determine current stage for sidebar
    if not st.session_state.get('candidate_info'):
        current_stage = 'info'
    elif not st.session_state.get('assessment_completed'):
        current_stage = 'assessment'
    else:
        current_stage = 'report'
    
    # Get resume analysis results if available
    resume_analysis = {
        'consistency_score': st.session_state.get('resume_consistency_score', 0),
        'strengths': st.session_state.get('resume_findings', []),
    } if 'resume_consistency_score' in st.session_state else None
    
    # Render sidebar with current stage and analysis
    render_sidebar(current_stage, resume_analysis)
    
    # Apply custom CSS theme
    st.markdown(get_custom_css(st.session_state.theme), unsafe_allow_html=True)
    
    # Language and Theme selectors in top bar
    col1, col2, col3 = st.columns([6, 2, 2])
    
    with col1:
        lang = st.session_state.language
        st.title(get_text('app_title', lang))
        st.markdown(get_text('welcome_message', lang))
        st.markdown(get_text('subtitle', lang))
    
    with col2:
        # Language selector
        languages = get_available_languages()
        selected_lang = st.selectbox(
            get_text('language_selector', st.session_state.language),
            options=list(languages.keys()),
            format_func=lambda x: languages[x],
            index=list(languages.keys()).index(st.session_state.language),
            key='lang_selector'
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()
    
    with col3:
        # Theme selector
        themes = get_available_themes()
        selected_theme = st.selectbox(
            get_text('theme_selector', st.session_state.language),
            options=list(themes.keys()),
            format_func=lambda x: themes[x],
            index=list(themes.keys()).index(st.session_state.theme),
            key='theme_selector'
        )
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()

    # Initialize LangChain components with automated persona selection
    try:
        # Validate the provided Groq API key and warn the user if it looks malformed
        from utils.validators import validate_groq_key
        provided_key = st.session_state.get('groq_api_key', '')
        if provided_key and not validate_groq_key(provided_key):
            st.warning("The Groq API key in Advanced Options looks malformed — the app may fall back to default Groq settings.")

        # Set the persona based on candidate info
        selected_persona = determine_optimal_persona(st.session_state.get('candidate_info', {}))
        st.session_state.selected_persona = selected_persona
        
        # Use simple ConversationChain for now as it handles memory statefully
        # In a full modern refactor we would switch to RunnableWithMessageHistory
        conversation_llm = LLMManager.get_llm(
            'conversation', 
            temperature=0.7, 
            max_tokens=2000,
            api_key=st.session_state.get('groq_api_key') or None,
            allow_local_models=st.session_state.get('allow_local_models', False)
        )
        
        # Create a lightweight conversation wrapper that applies the prompt template and
        # exposes an `invoke` method compatible with the rest of the code.
        prompt_template = get_persona_prompt(selected_persona)

        class ConversationWrapper:
            def __init__(self, prompt_template, llm):
                self.prompt_template = prompt_template
                self.llm = llm

            def _render_prompt(self, input_text, history):
                try:
                    # Try a few common formatting APIs
                    if hasattr(self.prompt_template, 'format'):
                        return self.prompt_template.format(input=input_text, history=history)
                    if hasattr(self.prompt_template, 'format_messages'):
                        messages = self.prompt_template.format_messages(input=input_text, history=history)
                        # Join messages as text when format_messages is used
                        return "\n".join(map(str, messages))
                except Exception:
                    pass
                return input_text

            def invoke(self, payload):
                if isinstance(payload, dict):
                    input_text = payload.get('input', '')
                    history = payload.get('history', [])
                else:
                    input_text = str(payload)
                    history = []

                prompt_text = self._render_prompt(input_text, history)

                # Prefer invoking with a dict-like payload; fall back to plain string if needed
                try:
                    return self.llm.invoke({"input": prompt_text, "history": history})
                except Exception:
                    return self.llm.invoke(prompt_text)

        conversation = ConversationWrapper(prompt_template, conversation_llm)

        # Display backend and key status for visibility
        try:
            backend = getattr(conversation_llm, '_backend', None) or getattr(conversation_llm, 'model_name', None) or 'Unavailable'
            key_ok = getattr(conversation_llm, '_key_format_valid', False)
            status_msg = f"Backend: {backend}"
            if key_ok:
                status_msg += " — API key format valid"
            else:
                if st.session_state.get('groq_api_key'):
                    status_msg += " — API key present but unverified or malformed"
                else:
                    status_msg += " — using default settings or stub"
            st.caption(status_msg)
        except Exception:
            pass
    except Exception as e:
        st.error(f"Error initializing AI components: {str(e)}")
        st.stop()

    # Phase 1: Initial Information Gathering
    if not st.session_state.candidate_info:
        with ui.card(key="candidate_info_card"):
            st.header('📋 Candidate Information')
            
            # Privacy Notice using alert component
            ui.alert(
                title="🔒 Privacy Notice",
                description="Your personal information will be used solely for this technical assessment. All data is stored temporarily in your browser session and will be deleted when you close the browser or reset the assessment. We do not permanently store your personal information on our servers.",
                key="privacy_alert"
            )
            
            # Resume upload section
            st.subheader("📄 Upload Your Resume")
            uploaded_file = st.file_uploader(
                "Upload Resume (PDF or DOCX) to Auto-fill Details", 
                type=['pdf', 'docx'],
                help="Upload your resume to automatically extract and fill in your information."
            )

            if uploaded_file is not None:
                # Check if we already processed this file to avoid loops
                file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}"
                if 'last_processed_file' not in st.session_state or st.session_state.last_processed_file != file_key:
                    with st.spinner("🔄 Analyzing resume and auto-filling details..."):
                        try:
                            resume_text = extract_text_from_resume(uploaded_file)
                            if not resume_text:
                                st.error("❌ Resume processing failed: file is empty or unreadable. Please re-upload a valid PDF or DOCX.")
                            else:
                                try:
                                    extracted_data = parse_resume_with_llm(resume_text)
                                    if extracted_data:
                                        # Update session state variables used by text_inputs
                                        st.session_state.full_name = extracted_data.get("Full Name", "")
                                        st.session_state.email = extracted_data.get("Email", "")
                                        st.session_state.phone = extracted_data.get("Phone", "")
                                        st.session_state.years_exp = extracted_data.get("Years of Experience", 0)
                                        st.session_state.desired_position = extracted_data.get("Desired Position", "")
                                        st.session_state.location = extracted_data.get("Location", "")
                                        
                                        tech_stack_list = extracted_data.get("Tech Stack", [])
                                        if isinstance(tech_stack_list, list):
                                            st.session_state.tech_stack = ", ".join(tech_stack_list)
                                        else:
                                            st.session_state.tech_stack = str(tech_stack_list)
                                        
                                        st.session_state.last_processed_file = file_key
                                        st.success("✅ Resume processed! Information auto-filled.")
                                        st.rerun()
                                    else:
                                        # LLM parsing was skipped or returned no usable JSON
                                        st.info("ℹ️ Resume parsing unavailable — API key not configured. You can still manually enter your information, or paste a Groq API key in Advanced Options to enable auto-fill.")
                                        st.session_state.resume_parse_skipped = True
                                except json.JSONDecodeError as je:
                                    st.warning(f"⚠️ Resume parsing returned invalid format: {str(je)[:100]}. Please manually enter your information.")
                                except Exception as e:
                                    st.warning(f"⚠️ Resume parsing encountered an error: {str(e)[:100]}. You can continue by manually entering your information.")
                        except Exception as e:
                            st.error(f"❌ Failed to process resume file: {str(e)[:150]}")

            # Form with shadcn-ui styling
            st.subheader("📝 Enter Your Information")
            with st.form('info_form'):
                col1, col2 = st.columns(2)
                
                with col1:
                    full_name = st.text_input('Full Name*', value=st.session_state.get('full_name', ''), placeholder="John Doe")
                    email = st.text_input('Email Address*', value=st.session_state.get('email', ''), placeholder="john@example.com")
                    phone = st.text_input('Phone Number*', value=st.session_state.get('phone', ''), placeholder="+1-555-0123")
                    years_exp = st.number_input('Years of Experience', min_value=0, max_value=50, step=1, value=st.session_state.get('years_exp', 0))
                
                with col2:
                    desired_position = st.text_input('Desired Position(s)*', value=st.session_state.get('desired_position', ''), placeholder="Senior Developer")
                    location = st.text_input('Current Location*', value=st.session_state.get('location', ''), placeholder="San Francisco, CA")
                    tech_stack = st.text_area('Tech Stack (e.g., Python, Django, JavaScript)*', value=st.session_state.get('tech_stack', ''), placeholder="Python, JavaScript, React, Django")
                
                st.markdown("---")
                st.caption("*Required fields are marked with an asterisk")
                
                # Use shadcn-ui button for submit
                submitted = st.form_submit_button('✅ Submit Information', use_container_width=True)

                if submitted:
                    # Validate all required fields
                    validation_errors = []

                    if not full_name.strip():
                        validation_errors.append("Full Name is required")
                    if not email.strip() or not validate_email(email):
                        validation_errors.append("Valid Email Address is required")
                    if not phone.strip() or not validate_phone(phone):
                        validation_errors.append("Valid Phone Number is required (e.g., +1-555-0123, (555) 123-4567)")
                    if not desired_position.strip():
                        validation_errors.append("Desired Position is required")
                    if not location.strip():
                        validation_errors.append("Location is required")
                    if not tech_stack.strip() or not validate_tech_stack(tech_stack):
                        validation_errors.append("At least one Technology in Tech Stack is required")
                    if not uploaded_file:
                        validation_errors.append("Resume is required")
                    if validation_errors:
                        with ui.element("div", className="space-y-2"):
                            ui.alert(
                                title="⚠️ Validation Errors",
                                description="Please fix the following errors:\n" + "\n".join(validation_errors),
                                key="validation_alert"
                            )
                    else:
                        resume_text = extract_text_from_resume(uploaded_file)
                        # Default values in case resume extraction failed or returned empty
                        consistency_score = 0.0
                        findings = []
                        if not resume_text:
                            ui.alert(
                                title="Error",
                                description="Resume processing failed: file is empty or unreadable. Please re-upload a valid PDF or DOCX.",
                                key="resume_error_alert"
                            )
                        else:
                            consistency_score, findings = analyze_resume_consistency(
                                resume_text,
                                {
                                    "Full Name": full_name,
                                    "Tech Stack": [tech.strip() for tech in tech_stack.split(',') if tech.strip()],
                                    "Years of Experience": years_exp,
                                    "Desired Position": desired_position
                                }
                            )
                        st.session_state.resume_consistency_score = consistency_score
                        st.session_state.resume_findings = findings
                        st.session_state.candidate_info = {
                            "Full Name": full_name,
                            "Email": email,
                            "Phone": phone,
                            "Years of Experience": years_exp,
                            "Desired Position": desired_position,
                            "Location": location,
                            "Tech Stack": [tech.strip() for tech in tech_stack.split(',') if tech.strip()]
                        }
                        st.success('✅ Information submitted successfully!')
                        st.rerun()

    # Phase 2: Technical Assessment
    elif not st.session_state.assessment_completed:
        with ui.card(key="assessment_card"):
            st.header('🎯 Technical Assessment')
            
            # Create a container for progress metrics
            progress_container = create_progress_container()
            
            # Initialize assessment state if needed
            if 'assessment_state' not in st.session_state:
                st.session_state.assessment_state = {
                    'internal_confidence': 0.0,
                    'admin_view': False  # Could be set based on authentication
                }
            
            # Add early completion option with hidden confidence
            if st.session_state.questions_asked > 0:
                col_comp1, col_comp2 = st.columns([4, 1])
                with col_comp2:
                    if ui.button(text='⏹️ Complete Now', key='complete_early'):
                        confidence, decision, _, _, reasoning = assess_confidence_level(
                            st.session_state.evaluation_scores,
                            st.session_state.answers,
                            conversation
                        )
                        
                        # Update internal state without displaying
                        st.session_state.confidence_level = confidence
                        st.session_state.current_decision = decision
                        st.session_state.assessment_completed = True
                        st.session_state.final_reasoning = reasoning
                        
                        # Show completion confirmation without revealing confidence
                        st.success("✅ Assessment completed successfully!")
                        st.rerun()
            
            # Update progress display
            update_assessment_progress(progress_container, st.session_state.assessment_state['admin_view'])
            
            # Progress indicator using tabs
            st.markdown("---")
            ui.tabs(
                options=[f'Q{i+1}' for i in range(min(st.session_state.questions_asked + 1, 15))],
                default_value=f'Q{st.session_state.questions_asked + 1}' if st.session_state.questions_asked < 15 else 'Q15',
                key="assessment_tabs"
            )
            
            # Generate or display current question
            if not st.session_state.current_question:
                if st.session_state.questions_asked == 0:
                    # Initial questions generation
                    tech_stack_str = ', '.join(st.session_state.candidate_info["Tech Stack"])
                    technical_questions = generate_technical_questions(tech_stack_str, conversation)
                    if not technical_questions:
                        ui.alert(
                            title="Error",
                            description="No technical questions generated. Please check the tech stack and try again.",
                            key="question_error"
                        )
                        st.stop()
                    st.session_state.technical_questions = technical_questions
                    st.session_state.current_question_index = 0
                    st.session_state.current_question = technical_questions[0]
                else:
                    # Generate focused question based on confidence assessment
                    confidence, decision, need_more, focus_areas, reasoning = assess_confidence_level(
                        st.session_state.evaluation_scores,
                        st.session_state.answers,
                        conversation
                    )
                    
                    # Update internal state without displaying
                    st.session_state.confidence_level = confidence
                    st.session_state.current_decision = decision
                    
                    # Check for assessment completion
                    if not need_more or st.session_state.questions_asked >= 15:
                        st.session_state.assessment_completed = True
                        st.session_state.final_reasoning = reasoning
                        st.success("✅ Assessment completed successfully!")
                        st.rerun()
                    
                    # Generate next question
                    previous_questions = list(st.session_state.answers.keys())
                    new_question = generate_focused_question(
                        st.session_state.candidate_info["Tech Stack"],
                        focus_areas,
                        previous_questions,
                        conversation
                    )
                    st.session_state.current_question = new_question
            
            # Display current question with card styling
            with ui.card(key=f"question_card_{st.session_state.questions_asked}"):
                col_q1, col_q2 = st.columns([5, 1])
                with col_q1:
                    st.subheader(f'Question {st.session_state.questions_asked + 1}')
                with col_q2:
                    st.caption(f"Question {st.session_state.questions_asked + 1}/15")
                
                st.markdown(st.session_state.current_question)
            
            # Answer input
            st.markdown("---")
            st.write("**Your Answer:**")
            answer = st.text_area('', 
                                value=st.session_state.get('current_answer', ''),
                                height=150, 
                                placeholder="Provide a detailed answer...",
                                key=f"answer_{st.session_state.questions_asked}")
            
            # Button group
            col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 3])
            
            with col_btn1:
                if ui.button(text='✅ Submit Answer', key='submit_answer'):
                    if not answer.strip():
                        st.warning('⚠️ Please provide an answer before submitting.')
                    else:
                        # Check for exit keywords
                        from assessment.question_generation import detect_exit_keywords
                        if detect_exit_keywords(answer):
                            st.info("🛑 Exit keyword detected. Completing assessment...")
                            st.session_state.assessment_completed = True
                            st.session_state.current_decision = "Early Exit"
                            st.session_state.final_reasoning = "Candidate requested to exit the assessment."
                            st.rerun()
                        
                        question = st.session_state.current_question
                        st.session_state.answers[question] = answer
                        
                        # Perform sentiment analysis with error handling
                        try:
                            sentiment_data = analyze_sentiment(answer)
                            st.session_state.sentiment_scores[question] = sentiment_data
                        except Exception as e:
                            st.warning(f"⚠️ Could not analyze sentiment: {str(e)[:80]}")
                            sentiment_data = {
                                'sentiment': 'neutral',
                                'confidence_score': 0.5,
                                'word_count': len(answer.split()),
                                'technical_depth': 'moderate',
                                'positive_indicators': [],
                                'uncertain_indicators': []
                            }
                        
                        # Evaluate answer with error handling
                        try:
                            score, feedback = evaluate_answer_with_llm(
                                question,
                                answer,
                                st.session_state.candidate_info.get("Tech Stack", "")
                            )
                            st.session_state.evaluation_scores[question] = score
                        except Exception as e:
                            st.error(f"❌ Error evaluating answer: {str(e)[:100]}")
                            st.info("💡 Using fallback evaluation...")
                            try:
                                from assessment.evaluation import fallback_evaluation
                                score, feedback = fallback_evaluation(question, answer)
                                st.session_state.evaluation_scores[question] = score
                            except Exception as fallback_err:
                                st.warning(f"⚠️ Fallback evaluation also failed: {str(fallback_err)[:80]}")
                                score = 0.5
                                feedback = ["Unable to evaluate at this time. Your answer has been recorded."]
                        
                        # Display results in cards
                        st.markdown("---")
                        st.markdown("### 📊 Answer Evaluation")
                        
                        col_metric1, col_metric2, col_metric3 = st.columns(3)
                        with col_metric1:
                            st.metric("Technical Score", f"{score*100:.1f}%")
                        with col_metric2:
                            st.metric("Response Confidence", f"{sentiment_data.get('confidence_score', 0.5)*100:.0f}%")
                        with col_metric3:
                            st.metric("Sentiment", f"{sentiment_data.get('sentiment', 'neutral')}")
                        
                        # Show feedback with color indicators
                        try:
                            if score >= 0.8:
                                st.success("✅ Excellent answer! Your response demonstrates strong technical knowledge.")
                            elif score >= 0.6:
                                st.info("ℹ️ Good answer. Your response shows competence with room for improvement.")
                            else:
                                st.warning("⚠️ Needs improvement. The answer could benefit from more technical depth and detail.")
                        except Exception as e:
                            st.debug(f"Alert display error: {e}")
                        
                        # Show sentiment feedback
                        try:
                            sentiment_feedback = get_sentiment_feedback(sentiment_data)
                            st.info(f"💬 Communication Analysis: {sentiment_feedback}")
                        except Exception as e:
                            st.debug(f"Sentiment feedback error: {e}")
                        
                        # Detailed feedback in expandable section
                        try:
                            with st.expander("📋 View Detailed Feedback"):
                                if feedback and isinstance(feedback, list):
                                    for point in feedback:
                                        st.write(f"• {point}")
                                else:
                                    st.write("Feedback: " + str(feedback))
                                
                                st.markdown("**📈 Response Metrics:**")
                                st.write(f"- Word Count: {sentiment_data.get('word_count', 0)}")
                                st.write(f"- Technical Depth: {sentiment_data.get('technical_depth', 'unknown')}")
                                st.write(f"- Confidence Indicators: {len(sentiment_data.get('positive_indicators', []))}")
                                st.write(f"- Uncertainty Indicators: {len(sentiment_data.get('uncertain_indicators', []))}")
                        except Exception as e:
                            st.debug(f"Feedback display error: {e}")
                        
                        # Update assessment state
                        st.session_state.questions_asked += 1
                        st.session_state.current_question = None
                        st.session_state.current_answer = ''
                        st.rerun()
            
            with col_btn2:
                if ui.button(text='⏭️ Skip Question', key='skip_question'):
                    question = st.session_state.current_question
                    st.session_state.answers[question] = "Skipped"
                    st.session_state.evaluation_scores[question] = 0.0
                    st.session_state.questions_asked += 1
                    st.session_state.current_question = None
                    st.session_state.current_answer = ''
                    
                    # Count skipped questions
                    skipped_count = sum(1 for ans in st.session_state.answers.values() if ans == "Skipped")
                    if skipped_count >= CONFIDENCE_THRESHOLDS['skip_threshold']:
                        st.warning("⚠️ Too many questions skipped. Completing assessment.")
                        st.session_state.current_decision = "No Hire"
                        st.session_state.assessment_completed = True
                    st.rerun()
    # Phase 3: Final Report and Recommendation
    else:
        with ui.card(key="report_card"):
            st.header('📊 Assessment Report')

            # Calculate overall metrics
            if st.session_state.evaluation_scores:
                total_score = sum(st.session_state.evaluation_scores.values())
                total_questions = len(st.session_state.technical_questions)
                avg_score = total_score / total_questions if total_questions > 0 else 0
            else:
                avg_score = 0

            # Generate recommendation based on comprehensive evaluation
            if len(st.session_state.evaluation_scores) > 0:
                recommendation = generate_final_recommendation_with_llm(
                    st.session_state.candidate_info,
                    st.session_state.answers,
                    st.session_state.evaluation_scores
                )
            else:
                recommendation = "No questions evaluated yet."

            st.session_state.recommendation = recommendation
            
            # Candidate Information Section
            with ui.card(key="candidate_card_report"):
                st.subheader('👤 Candidate Information')
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    for key in ['Full Name', 'Email', 'Phone']:
                        if key in st.session_state.candidate_info:
                            st.write(f"**{key}:** {st.session_state.candidate_info[key]}")
                
                with col_info2:
                    for key in ['Desired Position', 'Location', 'Years of Experience']:
                        if key in st.session_state.candidate_info:
                            st.write(f"**{key}:** {st.session_state.candidate_info[key]}")
                
                if 'Tech Stack' in st.session_state.candidate_info:
                    st.write(f"**Tech Stack:** {', '.join(st.session_state.candidate_info['Tech Stack'])}")

            st.markdown("---")

            # Technical Assessment Results
            with ui.card(key="results_card"):
                st.subheader('🎯 Technical Assessment Results')

                # Create metrics display using shadcn-ui
                col_metric1, col_metric2, col_metric3 = st.columns(3)
                with col_metric1:
                    st.metric(
                        label="Average Score",
                        value=f"{avg_score*100:.1f}%",
                        delta=f"{(avg_score-0.7)*100:.1f}%" if avg_score > 0.7 else f"{(avg_score-0.7)*100:.1f}%"
                    )
                with col_metric2:
                    st.metric(
                        label="Questions Completed",
                        value=f"{len(st.session_state.answers)}/{len(st.session_state.technical_questions)}"
                    )
                with col_metric3:
                    highest_score = max(st.session_state.evaluation_scores.values(), default=0)
                    st.metric(
                        label="Highest Score",
                        value=f"{highest_score*100:.1f}%"
                    )

            st.markdown("---")

            # Detailed question analysis with accordion
            with ui.card(key="analysis_card"):
                st.subheader('📋 Detailed Analysis')
                
                # Create accordion for each question
                data = []
                for idx, (question, answer) in enumerate(st.session_state.answers.items(), 1):
                    score = st.session_state.evaluation_scores.get(question, 0)
                    data.append({
                        "trigger": f"Question {idx} - Score: {score*100:.1f}%",
                        "content": f"**Question:** {question}\n\n**Answer:** {answer}\n\n**Score:** {score*100:.1f}%"
                    })
                
                if data:
                    ui.accordion(data=data, class_name=None, key="analysis_accordion")

            st.markdown("---")

            # Recommendation section with alert styling
            with ui.card(key="recommendation_card"):
                st.subheader('💡 Recommendation')
                
                # Determine recommendation style based on average score
                if avg_score >= 0.8:
                    ui.alert(
                        title="✅ Strong Candidate",
                        description=recommendation,
                        key="rec_excellent"
                    )
                elif avg_score >= 0.6:
                    ui.alert(
                        title="ℹ️ Qualified Candidate",
                        description=recommendation,
                        key="rec_good"
                    )
                else:
                    ui.alert(
                        title="⚠️ Needs Further Assessment",
                        description=recommendation,
                        key="rec_caution"
                    )

            st.markdown("---")

            # Download Options
            with ui.card(key="download_card"):
                st.subheader('📥 Download Report')
                
                # Generate report
                report = generate_report(
                    st.session_state.candidate_info,
                    st.session_state.answers,
                    st.session_state.evaluation_scores,
                    st.session_state.recommendation
                )

                # Add download buttons in columns
                col_down1, col_down2 = st.columns(2)
                
                with col_down1:
                    st.download_button(
                        label='📄 Download JSON Report',
                        data=report,
                        file_name=f"{st.session_state.candidate_info['Full Name'].replace(' ', '_')}_Assessment_Report.json",
                        mime='application/json',
                        use_container_width=True
                    )

                with col_down2:
                    # Create PDF-friendly format
                    pdf_report = f"""
TalentScout Assessment Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
CANDIDATE INFORMATION
================================================================================
{json.dumps(st.session_state.candidate_info, indent=2)}

================================================================================
TECHNICAL ASSESSMENT RESULTS
================================================================================
Average Score: {avg_score*100:.1f}%
Questions Completed: {len(st.session_state.answers)}/{len(st.session_state.technical_questions)}

================================================================================
DETAILED ANSWERS
================================================================================
"""
                    for idx, (question, answer) in enumerate(st.session_state.answers.items(), 1):
                        score = st.session_state.evaluation_scores.get(question, 0)
                        pdf_report += f"\nQuestion {idx}:\n{question}\n\nAnswer:\n{answer}\n\nScore: {score*100:.1f}%\n{'-'*80}\n"

                    pdf_report += f"""
================================================================================
RECOMMENDATION
================================================================================
{st.session_state.recommendation}
"""

                    st.download_button(
                        label='📄 Download Text Report',
                        data=pdf_report,
                        file_name=f"{st.session_state.candidate_info['Full Name'].replace(' ', '_')}_Assessment_Report.txt",
                        mime='text/plain',
                        use_container_width=True
                    )

    

if __name__ == '__main__':
    try:
        main()
    except KeyError as ke:
        st.error(f"❌ Configuration error: Missing required setting '{str(ke)}'")
        st.info("💡 Try refreshing the page or resetting the assessment using the sidebar.")
    except json.JSONDecodeError as je:
        st.error(f"❌ Data parsing error: {str(je)[:100]}")
        st.info("💡 The data received couldn't be parsed. Try again or contact support.")
    except Exception as e:
        import traceback
        st.error(f"❌ An unexpected error occurred: {str(e)}")
        st.warning("⚠️ Detailed error information (for debugging):")
        st.code(traceback.format_exc(), language="python")
        st.info("💡 Try the following steps:")
        st.info("1. Refresh the page (F5)")
        st.info("2. Clear cache and cookies")
        st.info("3. Check if your Groq API key is still valid in Advanced Options")
        st.info("4. Reset the assessment using the Reset button in the sidebar")