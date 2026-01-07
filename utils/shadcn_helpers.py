"""
Streamlit shadcn-ui Helper Functions
Provides convenient wrappers and utilities for using shadcn-ui components
"""

import streamlit as st
import streamlit_shadcn_ui as ui
from typing import List, Dict, Optional, Tuple


def create_info_card(title: str, description: str, key: str) -> None:
    """
    Create an information card with title and description
    
    Args:
        title: Card title
        description: Card content
        key: Unique key for Streamlit
    """
    with ui.card(key=key):
        st.markdown(f"### {title}")
        st.markdown(description)


def create_metric_cards(metrics: Dict[str, Tuple[str, str]]) -> None:
    """
    Create a row of metric cards
    
    Args:
        metrics: Dictionary where key is metric name, value is (value, unit) tuple
    """
    cols = st.columns(len(metrics))
    for idx, (metric_name, (metric_value, unit)) in enumerate(metrics.items()):
        with cols[idx]:
            st.metric(label=metric_name, value=metric_value, delta=unit)


def create_form_section(title: str, fields: Dict[str, Dict], key: str) -> Dict:
    """
    Create a form section with multiple input fields
    
    Args:
        title: Section title
        fields: Dictionary of field configurations
        key: Unique key for Streamlit
    
    Returns:
        Dictionary of field values
    """
    with ui.card(key=key):
        st.markdown(f"### {title}")
        
        results = {}
        with st.form(f"{key}_form"):
            for field_name, field_config in fields.items():
                field_type = field_config.get('type', 'text')
                placeholder = field_config.get('placeholder', '')
                required = field_config.get('required', False)
                
                field_label = f"{field_name}{'*' if required else ''}"
                
                if field_type == 'text':
                    results[field_name] = st.text_input(field_label, placeholder=placeholder)
                elif field_type == 'textarea':
                    results[field_name] = st.text_area(field_label, placeholder=placeholder)
                elif field_type == 'number':
                    min_val = field_config.get('min', 0)
                    max_val = field_config.get('max', 100)
                    step = field_config.get('step', 1)
                    results[field_name] = st.number_input(field_label, min_value=min_val, max_value=max_val, step=step)
                elif field_type == 'select':
                    options = field_config.get('options', [])
                    results[field_name] = st.selectbox(field_label, options=options)
            
            submitted = st.form_submit_button("✅ Submit", use_container_width=True)
        
        return results, submitted


def create_progress_badge(current: int, total: int, key: str) -> None:
    """
    Create a progress badge showing current/total
    
    Args:
        current: Current progress value
        total: Total progress value
        key: Unique key for Streamlit
    """
    percentage = (current / total) * 100 if total > 0 else 0
    ui.badges(
        badge_list=[(f"{current}/{total} ({percentage:.0f}%)", "default")],
        class_name="mb-2",
        key=key
    )
    st.progress(current / total if total > 0 else 0)


def create_status_indicator(status: str, key: str) -> None:
    """
    Create a status indicator with color-coded message
    
    Args:
        status: Status string ('success', 'warning', 'error', 'info')
        key: Unique key for Streamlit
    """
    if status.lower() == 'success':
        ui.alert(
            title="✅ Success",
            description="Operation completed successfully.",
            key=key
        )
    elif status.lower() == 'warning':
        ui.alert(
            title="⚠️ Warning",
            description="Please review this information.",
            key=key
        )
    elif status.lower() == 'error':
        ui.alert(
            title="❌ Error",
            description="Something went wrong. Please try again.",
            key=key
        )
    else:
        ui.alert(
            title="ℹ️ Information",
            description="Please note this information.",
            key=key
        )


def create_score_display(score: float, total: float = 1.0, key: str = "score") -> None:
    """
    Create a visual score display with progress bar
    
    Args:
        score: Current score value
        total: Total possible score (default 1.0 for percentage)
        key: Unique key for Streamlit
    """
    percentage = (score / total) * 100 if total > 0 else 0
    
    with ui.card(key=f"{key}_card"):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.progress(score / total if total > 0 else 0)
        with col2:
            st.metric("Score", f"{percentage:.1f}%")


def create_feature_list(title: str, features: List[str], key: str) -> None:
    """
    Create a list of features with bullet points
    
    Args:
        title: Section title
        features: List of feature strings
        key: Unique key for Streamlit
    """
    with ui.card(key=key):
        st.markdown(f"### {title}")
        for feature in features:
            st.markdown(f"• {feature}")


def create_question_card(question_number: int, total_questions: int, question_text: str, key: str) -> None:
    """
    Create a formatted question card
    
    Args:
        question_number: Current question number
        total_questions: Total number of questions
        question_text: The actual question text
        key: Unique key for Streamlit
    """
    with ui.card(key=key):
        col_q1, col_q2 = st.columns([5, 1])
        with col_q1:
            st.markdown(f"### Question {question_number}")
        with col_q2:
            st.caption(f"{question_number}/{total_questions}")
        
        st.markdown("---")
        st.markdown(question_text)


def create_badge_group(items: List[str], variant: str = "default", key: str = "badges") -> None:
    """
    Create a group of badges
    
    Args:
        items: List of badge text items
        variant: Badge variant ('default', 'secondary', 'outline', 'destructive')
        key: Unique key for Streamlit
    """
    badge_list = [(item, variant) for item in items]
    ui.badges(badge_list=badge_list, class_name="flex gap-2 flex-wrap", key=key)


def create_section_divider() -> None:
    """Create a visual section divider"""
    st.markdown("---")


def create_empty_state(icon: str, title: str, description: str, key: str) -> None:
    """
    Create an empty state display
    
    Args:
        icon: Emoji icon
        title: Empty state title
        description: Empty state description
        key: Unique key for Streamlit
    """
    with ui.card(key=key):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"<div style='text-align:center'>{icon}</div>", unsafe_allow_html=True)
            st.markdown(f"### {title}")
            st.markdown(f"<div style='text-align:center'>{description}</div>", unsafe_allow_html=True)


def create_timeline(events: List[Dict[str, str]], key: str) -> None:
    """
    Create a timeline of events
    
    Args:
        events: List of events with 'title' and 'description' keys
        key: Unique key for Streamlit
    """
    with ui.card(key=key):
        st.markdown("### Timeline")
        for idx, event in enumerate(events):
            st.markdown(f"**{idx + 1}. {event.get('title', 'Event')}**")
            st.caption(event.get('description', ''))
            if idx < len(events) - 1:
                st.markdown("↓")


def create_comparison_table(columns: List[str], rows: List[List[str]], key: str) -> None:
    """
    Create a comparison table
    
    Args:
        columns: Column headers
        rows: List of row data
        key: Unique key for Streamlit
    """
    with ui.card(key=key):
        # Create a simple markdown table
        header = "| " + " | ".join(columns) + " |"
        separator = "|" + "|".join(["-" * (len(col) + 2) for col in columns]) + "|"
        
        table = header + "\n" + separator
        for row in rows:
            table += "\n| " + " | ".join(row) + " |"
        
        st.markdown(table)


# Validation and Feedback Helpers

def show_validation_error(field: str, message: str, key: str) -> None:
    """Show a validation error for a specific field"""
    ui.alert(
        title=f"⚠️ {field} Error",
        description=message,
        key=key
    )


def show_success_feedback(message: str, key: str) -> None:
    """Show a success feedback message"""
    ui.alert(
        title="✅ Success",
        description=message,
        key=key
    )


def show_info_feedback(message: str, key: str) -> None:
    """Show an info feedback message"""
    ui.alert(
        title="ℹ️ Information",
        description=message,
        key=key
    )


def create_accordion_section(title: str, items: List[Dict[str, str]], key: str) -> None:
    """
    Create an accordion section with collapsible items
    
    Args:
        title: Section title
        items: List of dicts with 'title' and 'content' keys
        key: Unique key for Streamlit
    """
    with ui.card(key=f"{key}_card"):
        st.markdown(f"### {title}")
        
        accordion_data = [
            {
                "trigger": item.get('title', 'Item'),
                "content": item.get('content', '')
            }
            for item in items
        ]
        
        ui.accordion(data=accordion_data, class_name="w-full", key=key)
