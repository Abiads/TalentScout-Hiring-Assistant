#!/bin/bash
# Run the TalentScout Hiring Assistant with streamlit-shadcn-ui

echo "🚀 Starting TalentScout Hiring Assistant..."
echo ""
echo "Ensuring all dependencies are installed..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install or update requirements
pip install -r requirements.txt -q

echo ""
echo "✅ Dependencies ready!"
echo ""
echo "🌐 Launching application at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the streamlit app
streamlit run version_3.py
