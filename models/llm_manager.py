# Create a new file: llm_manager.py

# Optional dependency: try to import ChatGroq from langchain_groq, fall back to a lightweight stub
try:
    from langchain_groq import ChatGroq
except Exception:
    # Minimal stub of ChatGroq to allow tests/run-time behavior without the package installed.
    # The stub implements the minimal interface used by the project: constructor, with_fallbacks, and invoke.
    from types import SimpleNamespace

    class ChatGroq:
        def __init__(self, *args, **kwargs):
            self._model_name = kwargs.get("model_name", "groq_stub")

        def with_fallbacks(self, fallbacks):
            # For the stub we just return self; fallbacks are ignored but accepted.
            return self

        def invoke(self, prompt: str):
            # Return an object with a `content` attribute to mimic langchain response
            return SimpleNamespace(content=f"[stub response from {self._model_name}] {prompt}")

from typing import Optional, Dict, Any
import streamlit as st
import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import CONFIDENCE_THRESHOLDS
from utils.validators import validate_groq_key, sanitize_groq_key

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LLMManager:
    """
    Singleton class to manage LLM instances with different configurations.
    Provides centralized control over LLM creation and caching.

    get_llm accepts optional keyword arguments:
      - api_key: str (Groq API key). If not provided and running inside Streamlit, it will use st.session_state['groq_api_key'] when available.
      - allow_local_models: bool (default False). If True, LLMManager may attempt to load local HF models (may download large artifacts). Default is False to avoid unexpected downloads.

    Additional utility:
      - verify_api_key(api_key, timeout): perform a lightweight live check (best-effort) and return (ok: bool, message: str).
    """
    _instances: Dict[str, ChatGroq] = {}

    @classmethod
    def verify_api_key(cls, api_key: str, timeout: int = 3) -> (bool, str):
        """Lightweight verification of a Groq API key.

        This attempts to create a minimal ChatGroq client and run a short invoke to verify the key.
        It's best-effort and will return (ok, message). Avoid calling this frequently.
        """
        if not api_key:
            return False, "No key provided"
        # sanitize and quick local validation
        key, warnings = sanitize_groq_key(api_key)
        if not key:
            return False, "; ".join(warnings)
        try:
            # Try to instantiate a client and call a short prompt. Use the mini model to reduce cost.
            client = ChatGroq(api_key=key, model_name="groq/compound-mini")
            try:
                # Some clients may support `invoke` directly; else, this will raise and be caught below
                resp = client.invoke("Ping")
                # If resp has content, consider it valid
                if getattr(resp, 'content', None):
                    return True, "Key validated: model responded."
                return True, "Key appears valid (no content returned but no error)."
            except Exception as call_err:
                msg = str(call_err)
                # Detect common error classes/messages
                if 'rate limit' in msg.lower() or '429' in msg:
                    return False, "Rate limit or quota exceeded for this key."
                if '401' in msg or 'unauthorized' in msg.lower() or 'invalid' in msg.lower():
                    return False, "Authentication failed: invalid API key."
                # Fallback: return false but include message
                return False, f"Verification failed: {msg}"
        except Exception as e:
            msg = str(e)
            if '401' in msg or 'unauthorized' in msg.lower() or 'invalid' in msg.lower():
                return False, "Authentication failed: invalid API key."
            return False, f"Unable to create client for verification: {msg}"

    @classmethod
    def get_llm(cls, llm_type: str, **kwargs) -> Any:
        """
        Get or create an LLM instance based on type and configuration.

        Args:
            llm_type: Type of LLM configuration ('evaluation', 'conversation', 'recommendation', 'report')
            **kwargs: Optional override parameters for the LLM configuration
                - api_key: optional Groq API key to use
                - allow_local_models: optional bool to permit local HF model fallback
        Returns:
            ChatGroq or compatible LLM instance
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
        # Remove control keys from kwargs so they aren't forwarded to model constructors
        forwarded = {**base_configs.get(llm_type, {}), **kwargs}
        # Extract control params which should not be passed through
        api_key = forwarded.pop('api_key', None) or kwargs.get('api_key') or getattr(st.session_state, 'groq_api_key', None)
        allow_local = forwarded.pop('allow_local_models', False)
        local_model_id = forwarded.pop('local_model_id', None)

        # Build cache key from the forwarded settings (excluding sensitive or control keys)
        cache_key = f"{llm_type}_{hash(frozenset(forwarded.items()))}"

        # Return cached instance if it exists
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        # Early exit: if no API key and local models are not allowed, avoid attempting
        # to create Groq clients (which will log repeated errors) and instead return a
        # lightweight local stub that preserves the expected interface.
        if not api_key and not allow_local:
            log.info("No Groq API key provided and local models not allowed; using local stub LLM. Set a Groq API key in Advanced Options to enable Groq models.")
            from types import SimpleNamespace
            stub = SimpleNamespace(
                with_fallbacks=lambda fs: fs[0] if fs else None,
                invoke=lambda prompt: SimpleNamespace(content=f"[no-key-stub] {prompt}")
            )
            setattr(stub, '_backend', 'Local Stub (no key)')
            setattr(stub, '_key_format_valid', False)
            cls._instances[cache_key] = stub
            return stub

        try:
            # Extract basic processing params
            temperature = forwarded.pop('temperature', 0.7)
            max_tokens = forwarded.pop('max_tokens', None)

            # Move specific parameters to model_kwargs
            model_kwargs = {}
            for param in ['top_p', 'presence_penalty', 'frequency_penalty']:
                if param in forwarded:
                    model_kwargs[param] = forwarded.pop(param)

            # Create primary instance - prefer provided API key; if not provided pass None
            # Only pass explicit, known arguments to avoid accidental duplicate/unsupported kwargs
            try:
                if api_key and not validate_groq_key(api_key):
                    log.warning("Provided Groq API key appears malformed; continuing but the server may reject it.")

                # Use Groq Mini as primary for cost and stability
                primary_llm = ChatGroq(
                    api_key=api_key,
                    model_name=forwarded.get('model_name', "groq/compound-mini"),
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_kwargs=model_kwargs,
                )
            except TypeError as te:
                # Likely caused by unexpected constructor parameters; try a simpler constructor
                log.warning("ChatGroq constructor failed with TypeError, retrying with minimal args: %s", te)
                try:
                    primary_llm = ChatGroq(api_key=api_key, model_name="groq/compound-mini")
                except Exception as inner:
                    log.error("Primary ChatGroq creation failed unexpectedly: %s", inner)
                    primary_llm = None
            except Exception as e:
                log.error("Primary ChatGroq creation failed: %s", e)
                primary_llm = None

            # If primary_llm failed to be created, attempt fallback immediately
            if primary_llm is None:
                log.warning("Primary Groq client could not be created; attempting fallback Groq mini client.")
                try:
                    primary_llm = ChatGroq(api_key=api_key, model_name="groq/compound-mini")
                except Exception as e:
                    log.error("Fallback Groq mini client also failed: %s", e)
                    # Use a safe stub fallback if nothing else works
                    try:
                        from types import SimpleNamespace
                        primary_llm = SimpleNamespace(with_fallbacks=lambda fs: fs[0] if fs else None, invoke=lambda prompt: SimpleNamespace(content=f"[unavailable-lm] {prompt}"))
                        log.info("Using local SimpleNamespace stub as primary LLM due to previous failures.")
                    except Exception:
                        raise RuntimeError("Unable to create any LLM clients; check environment and dependencies.")
            
            # Create fallback instance. By default we do NOT download local models.
            # If `allow_local_models` is True, a local HF fallback may be attempted (NOT recommended by default).
            allow_local = kwargs.get('allow_local_models', False)

            if allow_local:
                try:
                    # Local imports to avoid hard dependency if not installed
                    from langchain_huggingface import HuggingFacePipeline
                    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                    import torch

                    # Note: This path may trigger large downloads (e.g., Qwen). Use with care.
                    model_id = local_model_id or "Qwen/Qwen2.5-1.5B-Instruct"
                    log.info("Attempting to load local fallback model: %s (may download large files)", model_id)

                    tokenizer = AutoTokenizer.from_pretrained(model_id)
                    model = AutoModelForCausalLM.from_pretrained(model_id)

                    pipe = pipeline(
                        "text-generation",
                        model=model,
                        tokenizer=tokenizer,
                        max_new_tokens=max_tokens or 512,
                        temperature=temperature,
                        top_p=model_kwargs.get('top_p', 0.95),
                        repetition_penalty=model_kwargs.get('frequency_penalty', 1.0) + 1.0,
                        device_map="auto" if torch.cuda.is_available() else "cpu"
                    )

                    fallback_llm = HuggingFacePipeline(pipeline=pipe)
                    log.info("Local fallback model loaded successfully.")

                except Exception as e:
                    log.warning("Local HF model failed to load (%s). Falling back to Groq Mini.", e)
                    try:
                        fallback_llm = ChatGroq(
                            api_key=api_key,
                            model_name="groq/compound-mini",
                            temperature=temperature,
                            max_tokens=max_tokens,
                            model_kwargs=model_kwargs,
                        )
                    except Exception as fallback_err:
                        log.error("Unable to create Groq mini fallback: %s", fallback_err)
                        # Final safe stub
                        from types import SimpleNamespace
                        fallback_llm = SimpleNamespace(invoke=lambda prompt: SimpleNamespace(content=f"[fallback-unavailable] {prompt}"))
            else:
                # Do not attempt to download or load local HF models — always use a Groq mini fallback
                try:
                    fallback_llm = ChatGroq(
                        api_key=api_key,
                        model_name="groq/compound-mini",
                        temperature=temperature,
                        max_tokens=max_tokens,
                        model_kwargs=model_kwargs,
                    )
                except Exception as e:
                    log.error("Groq mini fallback creation failed: %s", e)
                    from types import SimpleNamespace
                    fallback_llm = SimpleNamespace(invoke=lambda prompt: SimpleNamespace(content=f"[fallback-unavailable] {prompt}"))
            
            # Create LLM with fallback
            try:
                if hasattr(primary_llm, 'with_fallbacks'):
                    llm_with_fallback = primary_llm.with_fallbacks([fallback_llm])
                else:
                    # Wrap primary to provide `.with_fallbacks` if missing
                    class _Wrapper:
                        def __init__(self, primary, fb):
                            self.primary = primary
                            self._fb = fb
                        def with_fallbacks(self, fallbacks):
                            # Return an object that has invoke and content behavior. Prefer primary if works.
                            return self
                        def invoke(self, prompt):
                            try:
                                return self.primary.invoke(prompt)
                            except Exception:
                                return self._fb.invoke(prompt)
                    llm_with_fallback = _Wrapper(primary_llm, fallback_llm)
            except Exception as e:
                log.error("Failed to combine primary and fallback LLMs: %s", e)
                # As a last resort, use the fallback directly
                llm_with_fallback = fallback_llm
            
            # Attach lightweight metadata for UI introspection
            try:
                backend_name = 'unknown'
                # Primary type checks
                if hasattr(primary_llm, '_model_name'):
                    backend_name = f"Stub ({primary_llm._model_name})"
                elif hasattr(primary_llm, 'model_name'):
                    backend_name = f"Groq ({getattr(primary_llm, 'model_name')})"
                else:
                    backend_name = "Groq Mini"

                setattr(llm_with_fallback, '_backend', backend_name)
                setattr(llm_with_fallback, '_key_format_valid', bool(api_key and validate_groq_key(api_key)))
            except Exception:
                pass

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
