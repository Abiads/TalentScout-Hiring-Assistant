import streamlit as st
import streamlit_shadcn_ui as ui
from config.settings import CONFIDENCE_THRESHOLDS

def create_progress_container():
    """Creates a container for progress metrics that can be updated dynamically"""
    return st.empty()
    
def get_display_metrics(is_admin_view=False):
    """
    Determines which metrics to display based on user type.
    Returns a dictionary of metrics that should be visible.
    """
    metrics = {
        "questions_asked": st.session_state.questions_asked,
    }
    
    if is_admin_view and 'confidence_level' in st.session_state:
        metrics["confidence_level"] = st.session_state.confidence_level
        metrics["current_decision"] = st.session_state.get('current_decision', 'In Progress')
    
    return metrics

def update_assessment_progress(container, is_admin_view=False):
    """
    Updates the assessment progress display using shadcn-ui components.
    Uses a separate container to manage visibility.
    """
    metrics = get_display_metrics(is_admin_view)
    
    with container:
        container.empty()  # Clear previous content
        
        # Create progress card
        with ui.card(key="progress_metrics_card"):
            st.markdown("### 📊 Assessment Progress")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Questions Asked", metrics["questions_asked"], f"of 15")
            
            with col2:
                # Progress percentage
                progress_pct = (metrics["questions_asked"] / 15) * 100
                st.metric("Completion", f"{progress_pct:.0f}%")
                st.progress(metrics["questions_asked"] / 15)
            
            with col3:
                if is_admin_view and "confidence_level" in metrics:
                    st.metric("Internal Confidence", f"{metrics['confidence_level']*100:.1f}%")
                else:
                    st.metric("Status", "In Progress")
        
        # Display focus areas if available
        if is_admin_view and "confidence_level" in metrics:
            st.markdown("---")
            with ui.card(key="confidence_card"):
                st.markdown("### 🎯 Assessment Status")
                decision = metrics.get("current_decision", "In Progress")
                
                if decision == "Strong":
                    ui.alert(
                        title="✅ Strong Performance",
                        description="The candidate is performing well. Continue with standard assessment.",
                        key="status_strong"
                    )
                elif decision == "Borderline":
                    ui.alert(
                        title="⚠️ Borderline Performance",
                        description="The candidate is showing mixed results. Focused questions will help clarify.",
                        key="status_borderline"
                    )
                elif decision == "No Hire":
                    ui.alert(
                        title="❌ No Hire",
                        description="Based on current performance, the candidate does not meet requirements.",
                        key="status_nohire"
                    )
                else:
                    st.write(f"**Status:** {decision}")    