# Streamlit-shadcn-ui Integration Guide

## Overview

This project has been enhanced with **streamlit-shadcn-ui**, a modern UI component library for Streamlit that brings professional shadcn/ui components to your Streamlit application.

## Installation

The `streamlit-shadcn-ui` package has been added to `requirements.txt`. Install all dependencies using:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install streamlit-shadcn-ui
```

## Key Components Used

### 1. **Card Component** (`ui.card`)
Used for visual grouping and organization of content sections.

```python
with ui.card(key="unique_card_id"):
    st.header("Card Title")
    st.write("Card content goes here")
```

### 2. **Alert Component** (`ui.alert`)
Displays informational, warning, success, or error messages with visual styling.

```python
ui.alert(
    title="Alert Title",
    description="Alert message content",
    key="unique_alert_id"
)
```

### 3. **Button Component** (`ui.button`)
Styled button with enhanced appearance and better interactivity.

```python
if ui.button(text="Click Me", key="unique_button_id"):
    # Handle button click
    pass
```

### 4. **Accordion Component** (`ui.accordion`)
Collapsible sections for organizing detailed information.

```python
data = [
    {"trigger": "Section 1", "content": "Content 1"},
    {"trigger": "Section 2", "content": "Content 2"},
]
ui.accordion(data=data, key="unique_accordion_id")
```

### 5. **Badges Component** (`ui.badges`)
Visual badges for tagging and categorization.

```python
ui.badges(
    badge_list=[("Tag1", "default"), ("Tag2", "secondary")],
    class_name="flex gap-2",
    key="unique_badges_id"
)
```

### 6. **Tabs Component** (`ui.tabs`)
Navigation tabs for organizing content.

```python
ui.tabs(
    options=['Tab1', 'Tab2', 'Tab3'],
    default_value='Tab1',
    key="unique_tabs_id"
)
```

### 7. **Element Component** (`ui.element`)
Advanced component for creating custom HTML/React elements with Tailwind CSS.

```python
with ui.element("div", className="flex gap-4", key="container"):
    ui.element("h2", className="text-lg font-bold", children=["Title"])
    ui.element("p", children=["Paragraph content"])
```

## File Structure

### Updated Files:

1. **version_3.py**
   - Main application file
   - Integrated shadcn-ui components throughout all three phases
   - Enhanced visual feedback and user experience
   - Better structured forms and cards

2. **components/sidebar.py**
   - Sidebar component using shadcn-ui
   - Better organized advanced options
   - Improved API key management UI
   - Visual status indicators

3. **components/progress.py**
   - Progress tracking with shadcn-ui cards
   - Enhanced metrics display
   - Visual progress indicators
   - Status alerts

4. **utils/shadcn_helpers.py** (New)
   - Reusable helper functions for shadcn-ui components
   - Wrapper functions for common patterns
   - Validation and feedback helpers
   - Utility functions for creating consistent UI

## Usage Examples

### Creating a Form Section

```python
from utils.shadcn_helpers import create_form_section

fields = {
    "name": {"type": "text", "placeholder": "Enter your name", "required": True},
    "email": {"type": "text", "placeholder": "Enter your email", "required": True},
    "experience": {"type": "number", "min": 0, "max": 50, "required": False},
}

results, submitted = create_form_section("Personal Info", fields, "personal_form")
if submitted:
    # Process form data
    pass
```

### Creating Metric Cards

```python
from utils.shadcn_helpers import create_metric_cards

metrics = {
    "Score": ("85.5%", "↑ 5%"),
    "Progress": ("42/50", "84%"),
    "Status": ("Active", "✓")
}

create_metric_cards(metrics)
```

### Creating a Progress Badge

```python
from utils.shadcn_helpers import create_progress_badge

create_progress_badge(current=5, total=15, key="progress_5_15")
```

### Creating an Accordion

```python
from utils.shadcn_helpers import create_accordion_section

items = [
    {"title": "Question 1", "content": "Answer 1: This is detailed feedback..."},
    {"title": "Question 2", "content": "Answer 2: More detailed feedback..."},
]

create_accordion_section("Assessment Results", items, "results_accordion")
```

## Component Styling

### Tailwind CSS Classes

The library uses Tailwind CSS for styling. Common classes used:

- `flex` - Flexbox layout
- `gap-2`, `gap-4` - Spacing between items
- `text-lg`, `text-sm` - Text sizing
- `font-bold`, `font-medium` - Font weights
- `rounded-md` - Border radius
- `w-full`, `h-full` - Width/height utilities
- `bg-blue-500`, `text-red-600` - Colors

### Custom Styling

Add custom CSS using `st.markdown`:

```python
st.markdown("""
<style>
    .custom-class {
        background-color: #f3f4f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)
```

## Color Variants

Components support various color variants:

- `default` - Default/neutral
- `secondary` - Secondary color
- `outline` - Outlined style
- `destructive` - Error/danger (red)
- `success` - Success (green)
- `warning` - Warning (yellow)

## Key Benefits

1. **Professional Appearance** - Modern, polished UI design
2. **Consistent Components** - Standardized across the application
3. **Better UX** - Enhanced interactivity and feedback
4. **Accessibility** - Built-in accessibility features
5. **Responsive Design** - Mobile-friendly layouts
6. **Easy to Extend** - Helper functions for reusability

## Migration Notes

### Before (Standard Streamlit):
```python
st.button("Submit")
st.info("Information message")
st.success("Success message")
```

### After (shadcn-ui):
```python
if ui.button(text="Submit", key="submit_btn"):
    pass

ui.alert(title="Information", description="...", key="info_1")
ui.alert(title="Success", description="...", key="success_1")
```

## Performance Considerations

- shadcn-ui components are optimized for performance
- Use `key` parameters to ensure stable component identity
- Avoid recreating component structures in loops
- Use `st.session_state` for state management

## Troubleshooting

### Issue: Components not displaying

**Solution:** Ensure `streamlit-shadcn-ui` is installed and imported correctly.

```python
import streamlit_shadcn_ui as ui
```

### Issue: Key conflicts

**Solution:** Always provide unique `key` parameters for each component.

```python
# Wrong - same key used multiple times
for i in range(3):
    ui.button(text="Click", key="btn")

# Correct - unique keys
for i in range(3):
    ui.button(text="Click", key=f"btn_{i}")
```

### Issue: Styling not applied

**Solution:** Verify Tailwind CSS class names are correct and use `className` parameter (camelCase).

```python
ui.element("div", className="flex gap-4 p-4", key="container")
```

## Resources

- **Official Documentation:** https://github.com/ObservedObserver/streamlit-shadcn-ui
- **shadcn/ui Components:** https://ui.shadcn.com/
- **Streamlit Documentation:** https://docs.streamlit.io/
- **Tailwind CSS:** https://tailwindcss.com/

## Contributing

When adding new features, consider:

1. Creating corresponding helper functions in `utils/shadcn_helpers.py`
2. Using consistent component structure and styling
3. Adding proper type hints and documentation
4. Testing components across different screen sizes

## License

This project integrates shadcn-ui, which is licensed under MIT. See LICENSE for details.
