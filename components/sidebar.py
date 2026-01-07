import streamlit as st
import streamlit_shadcn_ui as ui
from utils.resume_processing import generate_motivation_message
from config.settings import CONFIDENCE_THRESHOLDS
from models.llm_manager import LLMManager

def create_badge(text: str, variant: str = "default"):
    """Create a single badge using the badges component (workaround for ui.badge not existing)"""
    try:
        ui.badges(badge_list=[(text, variant)], class_name="my-1", key=f"badge_{text[:20]}")
    except Exception as e:
        # Fallback: just display text as markdown if badges fails
        st.markdown(f"🏷️ {text}")

def create_assessment_guidelines():
    """Create consistent assessment guidelines for sidebar"""
    guidelines = {
        "steps": [
            "Initial Information Collection",
            "Resume Analysis and Verification",
            "Technical Skills Assessment",
            "Performance Evaluation",
            "Final Report Generation"
        ],
        "rules": [
            "Answer each question thoroughly and precisely",
            "Take time to structure your responses clearly",
            "Focus on practical experience and examples",
            "Be honest about knowledge limitations",
            "Maintain professional communication"
        ]
    }
    return guidelines

def render_sidebar(stage, resume_analysis=None):
    """Render consistent sidebar content across all stages"""
    with st.sidebar:
        # Header with icon
        col_header1, col_header2 = st.columns([5, 1])
        with col_header1:
            st.header('📋 Assessment Guide')
        
        # Display current stage using badge-like styling
        stages = {
            'info': '📝 Information Collection',
            'assessment': '🎯 Technical Assessment',
            'report': '📊 Final Report'
        }
        current_stage = stages.get(stage, '')
        
        with ui.card(key="stage_card"):
            st.markdown(f"**Current Stage:** `{current_stage}`")
        
        st.markdown("---")
        
        # Display guidelines using accordion
        guidelines = create_assessment_guidelines()
        
        steps_data = [
            {
                "trigger": f"{'→ ' if stages[stage] in step else ''}{idx}. {step}",
                "content": f"Step {idx}: {step}\n\nThis is an important phase of the technical assessment process."
            }
            for idx, step in enumerate(guidelines['steps'], 1)
        ]
        
        ui.accordion(data=steps_data, class_name="w-full", key="steps_accordion")
        
        st.markdown("---")
        
        # Rules section with badges
        st.subheader("📋 Assessment Rules")
        for rule in guidelines['rules']:
            ui.badges(badge_list=[(rule, "default")], class_name="my-1", key=f"rule_{rule[:10]}")
        
        st.markdown("---")
        
        # Display motivation if resume has been analyzed
        if resume_analysis and 'consistency_score' in resume_analysis:
            st.subheader("🚀 Your Assessment Journey")
            motivation = generate_motivation_message(resume_analysis)
            
            with ui.card(key="motivation_card"):
                st.markdown(f"*{motivation}*")
                
                # Progress indicator
                consistency = resume_analysis.get('consistency_score', 0)
                st.write(f"**Resume Consistency:** {consistency*100:.1f}%")
                st.progress(consistency)
        
        st.markdown("---")
        
        # Advanced options section
        with st.expander("⚙️ Advanced Options", expanded=False):
            st.markdown("**Configure AI Settings**")
            st.markdown("Customize your Groq API configuration for this session.")
            
            # Use a separate input widget so we can programmatically set the active key only after verification
            groq_input = st.text_input(
                "🔑 Groq API Key",
                value=st.session_state.get('groq_api_key', ''),  # Use groq_api_key as source of truth
                key='groq_api_input',
                help='Paste your Groq API key here (starts with "gsk_").',
                type='password'
            )

            from utils.validators import validate_groq_key, sanitize_groq_key

            # Detect multiple keys or malformed input
            sanitized_key, sanitize_warnings = sanitize_groq_key(groq_input)
            if sanitize_warnings:
                for w in sanitize_warnings:
                    st.caption(f"⚠️ {w}")

            # Visual status line (based on the input box, not the saved active key)
            if not groq_input:
                st.caption("Status: No key provided — using default settings.")
            elif validate_groq_key(sanitized_key or groq_input):
                create_badge("✅ Valid", "default")
                st.success("Status: API key looks properly formatted.", icon="✅")
            else:
                create_badge("⚠️ Invalid", "destructive")
                st.warning("Status: API key looks malformed — check and try again.", icon="⚠️")

            # Verify key button
            col_verify1, col_verify2 = st.columns([1, 1])
            with col_verify1:
                if st.button("🔍 Verify Key", use_container_width=True):
                    # Use sanitized key if available
                    key_to_test = sanitized_key or groq_input
                    ok, message = LLMManager.verify_api_key(key_to_test)
                    if ok:
                        st.success(f"✅ {message}")
                        # Save verified key as the active session key (separate from the input widget)
                        # Do NOT modify groq_api_input as it's tied to the text input widget
                        st.session_state['groq_api_key'] = key_to_test
                        st.rerun()
                    else:
                        st.error(f"❌ Verification failed: {message}")
            
            with col_verify2:
                if st.button("🔄 Clear Key", use_container_width=True):
                    st.session_state['groq_api_key'] = ''
                    # Clear the input box by clearing its session state before the widget is created
                    # This will be done on next rerun via default value
                    st.info("API key cleared.")
                    st.rerun()
            
            st.markdown("---")
            
            # Local models option
            allow_local = st.checkbox(
                "⚙️ Allow local model fallback",
                value=st.session_state.get('allow_local_models', False),
                key='allow_local_models',
                help='Only enable if you want to download and use local models (may consume significant disk space).'
            )
            
            st.markdown("---")
            st.markdown("**💡 Quick Tips:**")
            st.markdown("- Local models are **large** — keep this off unless needed")
            st.markdown("- API keys are **session-only** — never persisted to disk")
            st.markdown("- [Get a Groq API key](https://console.groq.com/keys)")
        
        st.markdown("---")
        
        # Reset button at bottom
        if st.button('🔄 Reset Assessment', use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.info("Assessment reset. Refresh the page to start again.")
            st.rerun()
