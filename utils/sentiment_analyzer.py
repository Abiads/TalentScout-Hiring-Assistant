"""Sentiment Analysis Module - TalentScout Hiring Assistant

Analyzes candidate responses for sentiment, confidence, and emotional tone.
"""

import re
from typing import Dict, Tuple

def analyze_sentiment(text: str) -> Dict[str, any]:
    """
    Analyze sentiment of candidate's answer
    Returns sentiment score, confidence level, and emotional indicators
    """
    text_lower = text.lower().strip()
    
    # Positive indicators
    positive_words = ['confident', 'sure', 'definitely', 'absolutely', 'certainly', 
                     'experience', 'implemented', 'developed', 'created', 'built',
                     'successfully', 'achieved', 'optimized', 'improved']
    
    # Negative/uncertain indicators
    uncertain_words = ['maybe', 'perhaps', 'might', 'possibly', 'not sure', 
                      'i think', 'probably', 'guess', 'unsure', 'unclear']
    
    # Filler words (reduce confidence)
    filler_words = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'literally']
    
    # Count indicators
    positive_count = sum(1 for word in positive_words if word in text_lower)
    uncertain_count = sum(1 for word in uncertain_words if word in text_lower)
    filler_count = sum(1 for word in filler_words if word in text_lower)
    
    # Calculate word count and sentence count
    word_count = len(text.split())
    sentence_count = len(re.split(r'[.!?]+', text))
    
    # Calculate confidence score (0-1)
    confidence_score = 0.5  # Base score
    
    # Adjust based on positive indicators
    confidence_score += min(positive_count * 0.05, 0.3)
    
    # Penalize for uncertainty
    confidence_score -= min(uncertain_count * 0.1, 0.3)
    
    # Penalize for excessive fillers
    confidence_score -= min(filler_count * 0.05, 0.2)
    
    # Bonus for detailed answers (but not too long)
    if 20 <= word_count <= 150:
        confidence_score += 0.1
    elif word_count > 200:
        confidence_score -= 0.05  # Too verbose might indicate uncertainty
    
    # Ensure score is between 0 and 1
    confidence_score = max(0.0, min(1.0, confidence_score))
    
    # Determine sentiment category
    if confidence_score >= 0.7:
        sentiment = "Confident"
        emoji = "🟢"
    elif confidence_score >= 0.5:
        sentiment = "Moderate"
        emoji = "🟡"
    else:
        sentiment = "Uncertain"
        emoji = "🔴"
    
    # Detect technical depth indicators
    technical_indicators = ['algorithm', 'complexity', 'optimization', 'architecture',
                           'design pattern', 'framework', 'library', 'api', 'database',
                           'performance', 'scalability', 'security']
    
    technical_depth = sum(1 for indicator in technical_indicators if indicator in text_lower)
    
    return {
        "confidence_score": round(confidence_score, 2),
        "sentiment": sentiment,
        "emoji": emoji,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "technical_depth": technical_depth,
        "positive_indicators": positive_count,
        "uncertain_indicators": uncertain_count,
        "filler_count": filler_count
    }

def get_sentiment_feedback(sentiment_data: Dict) -> str:
    """Generate human-readable feedback based on sentiment analysis"""
    score = sentiment_data["confidence_score"]
    sentiment = sentiment_data["sentiment"]
    
    feedback_parts = []
    
    # Main sentiment feedback
    if sentiment == "Confident":
        feedback_parts.append("Your response shows strong confidence and clarity.")
    elif sentiment == "Moderate":
        feedback_parts.append("Your response shows moderate confidence.")
    else:
        feedback_parts.append("Your response could benefit from more confident language.")
    
    # Technical depth feedback
    if sentiment_data["technical_depth"] >= 3:
        feedback_parts.append("Good use of technical terminology.")
    elif sentiment_data["technical_depth"] == 0:
        feedback_parts.append("Consider using more technical terms to demonstrate depth.")
    
    # Length feedback
    if sentiment_data["word_count"] < 10:
        feedback_parts.append("Try to provide more detailed explanations.")
    elif sentiment_data["word_count"] > 200:
        feedback_parts.append("Consider being more concise in your responses.")
    
    # Filler words feedback
    if sentiment_data["filler_count"] > 3:
        feedback_parts.append("Reduce filler words for clearer communication.")
    
    return " ".join(feedback_parts)
