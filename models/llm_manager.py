# Create a new file: llm_manager.py

from langchain_groq import ChatGroq
from typing import Optional, Dict, Any
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import CONFIDENCE_THRESHOLDS

class LLMManager:
    """
    Singleton class to manage LLM instances with different configurations.
    Provides centralized control over LLM creation and caching.
    """
    _instances: Dict[str, ChatGroq] = {}
    
    @classmethod
    def get_llm(cls, llm_type: str, **kwargs) -> Any:
        """
        Get or create an LLM instance based on type and configuration.
        
        Args:
            llm_type: Type of LLM configuration ('evaluation', 'conversation', 'recommendation', 'report')
            **kwargs: Optional override parameters for the LLM configuration
            
        Returns:
            ChatGroq: Configured LLM instance
        """
        # Define base configurations for different LLM types
        base_configs = {
            'evaluation': {
                'temperature': 0.4,
                'max_tokens': 4028,
                'top_p': 0.95,
                'presence_penalty': 0.6,
                'frequency_penalty': 0.3
            },
            'conversation': {
                'temperature': 0.7,
                'max_tokens': 2000,
                'top_p': 1.0,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'recommendation': {
                'temperature': 0.5,
                'max_tokens': 4028,
                'top_p': 0.9,
                'presence_penalty': 0.4,
                'frequency_penalty': 0.4
            },
            'report': {
                'temperature': 0.3,
                'max_tokens': 4028,
                'top_p': 0.8,
                'presence_penalty': 0.2,
                'frequency_penalty': 0.2
            }
        }
        
        # Create cache key based on configuration
        config = {**base_configs.get(llm_type, {}), **kwargs}
        cache_key = f"{llm_type}_{hash(frozenset(config.items()))}"
        
        # Return cached instance if it exists
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        try:
            # Extract basic processing params
            temperature = config.pop('temperature', 0.7)
            max_tokens = config.pop('max_tokens', None)
            
            # Move specific parameters to model_kwargs
            model_kwargs = {}
            for param in ['top_p', 'presence_penalty', 'frequency_penalty']:
                if param in config:
                    model_kwargs[param] = config.pop(param)
            
            # Create primary instance
            primary_llm = ChatGroq(
                api_key="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",
                model_name="groq/compound",
                temperature=temperature,
                max_tokens=max_tokens,
                model_kwargs=model_kwargs,
                **config
            )
            
            # Create fallback instance using Local Hugging Face Model
            try:
                # Local imports to avoid hard dependency if not installed
                from langchain_huggingface import HuggingFacePipeline
                from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                import torch

                # Using Qwen2.5-1.5B-Instruct as it's a high-quality small instruction model
                # suitable for chat/assessment, significantly better than translation-only models.
                model_id = "Qwen/Qwen2.5-1.5B-Instruct"
                
                print(f"Loading local fallback model: {model_id}...")
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForCausalLM.from_pretrained(model_id)

                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=max_tokens or 512,
                    temperature=temperature,
                    top_p=model_kwargs.get('top_p', 0.95),
                    repetition_penalty=model_kwargs.get('frequency_penalty', 1.0) + 1.0, # Approximate mapping
                    device_map="auto" if torch.cuda.is_available() else "cpu"
                )
                
                fallback_llm = HuggingFacePipeline(pipeline=pipe)
                print("Local fallback model loaded successfully.")
                
            except Exception as e:
                print(f"Note: Local HF model failed to load ({str(e)}). Using Groq Mini as backup.")
                fallback_llm = ChatGroq(
                    api_key="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",
                    model_name="groq/compound-mini",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_kwargs=model_kwargs,
                    **config
                )
            
            # Create LLM with fallback
            llm_with_fallback = primary_llm.with_fallbacks([fallback_llm])
            
            cls._instances[cache_key] = llm_with_fallback
            return llm_with_fallback
            
        except Exception as e:
            raise RuntimeError(f"Failed to create LLM instance: {str(e)}")
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached LLM instances"""
        cls._instances.clear()


def determine_optimal_persona(candidate_info):
            if not candidate_info:
                return 'Default'
            
            years_exp = candidate_info.get('Years of Experience', 0)
            position = candidate_info.get('Desired Position', '').lower()
            tech_stack = candidate_info.get('Tech Stack', [])
            
            # Senior/Architect positions or 8+ years experience get Expert persona
            if years_exp >= 8 or any(role in position for role in ['senior', 'lead', 'architect', 'principal']):
                return 'Expert'
            
            # Research/Innovation roles or complex tech stack get Analytical persona
            if any(role in position for role in ['research', 'data', 'ml', 'ai']) or \
               any(tech in ['machine learning', 'ai', 'data science'] for tech in tech_stack):
                return 'Analytical'
            
            # Design/UI/Creative roles get Creative persona
            if any(role in position for role in ['design', 'ui', 'ux', 'frontend', 'creative']):
                return 'Creative'
            
            # Default for other cases
            return 'Default'

# Define persona-based prompt templates
def get_persona_prompt(persona):
    personas = {
    'Default': ChatPromptTemplate.from_messages([
        ("system", """You are a friendly and professional hiring assistant. 
                     Your role is to conduct preliminary technical screenings for candidates. 
                     Focus on gathering essential details, maintaining a conversational tone, 
                     and assessing both technical knowledge and problem-solving abilities. 
                     Provide constructive feedback without overwhelming the candidate."""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]),
    
    'Expert': ChatPromptTemplate.from_messages([
        ("system", """You are a highly experienced technical hiring manager. 
                     Your job is to assess candidates thoroughly on:
                     - Technical accuracy
                     - Problem-solving strategies
                     - Code quality and optimization
                     - System design and scalability
                     Start with foundational questions, then dive into advanced topics 
                     and edge cases. Offer precise, actionable feedback based on the 
                     candidate's responses, highlighting strengths and improvement areas."""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]),
    
    'Creative': ChatPromptTemplate.from_messages([
        ("system", """You are an engaging and innovative interviewer who evaluates 
                     candidates through real-world scenarios and practical challenges. 
                     Assess:
                     - Creative problem-solving
                     - Adaptability to unique scenarios
                     - Application of technical knowledge
                     - Clear and concise communication
                     Use situational questions and collaborative problem-solving exercises 
                     to encourage critical thinking."""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]),

    'Analytical': ChatPromptTemplate.from_messages([
        ("system", """You are a data-driven and analytical evaluator. 
                     Your focus is on assessing logical reasoning and analytical skills 
                     alongside technical expertise. Start with short and specific 
                     questions, progressing to scenarios that require deeper analysis. 
                     Evaluate based on:
                     - Clarity in logic
                     - Efficiency in problem-solving
                     - Ability to break down complex problems into manageable steps."""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]),
}
    return personas.get(persona, personas['Default'])
