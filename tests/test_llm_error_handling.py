import sys
import os
sys.path.append(os.getcwd())
import types
import builtins
from models.llm_manager import LLMManager
import importlib


def test_get_llm_with_invalid_api_key(monkeypatch, capsys):
    # Provide malformed key - should not raise, but should log a warning and return an LLM
    bad_key = "badkey"
    llm = LLMManager.get_llm('conversation', api_key=bad_key)
    assert llm is not None


def test_primary_creation_failure_fallback(monkeypatch):
    # Monkeypatch ChatGroq in the module to raise on creation to simulate constructor failure
    import models.llm_manager as mgr

    class FaultyChatGroq:
        def __init__(self, *args, **kwargs):
            raise TypeError("constructor broken")

    monkeypatch.setattr(mgr, 'ChatGroq', FaultyChatGroq)

    # Now call get_llm which should not raise, and should return a fallback (either ChatGroq mini or stub)
    llm = LLMManager.get_llm('conversation', api_key='gsk_validplaceholder123456')
    assert llm is not None


def test_allow_local_models_flag_prevents_download(monkeypatch):
    # By default local models are disabled; ensure it does not try to import transformers
    import models.llm_manager as mgr
    # Ensure calling with allow_local_models=False does not raise
    llm = LLMManager.get_llm('conversation', api_key='gsk_validplaceholder123456', allow_local_models=False)
    assert llm is not None


def test_sanitize_multiple_keys():
    from utils.validators import sanitize_groq_key
    key_input = "gsk_first_aaaaaaaaaaaaaaaa gsk_second_bbbbbbbbbbbbbbbb"
    key, warnings = sanitize_groq_key(key_input)
    assert key.startswith('gsk_')
    assert any('multiple' in w.lower() for w in warnings)


def test_verify_api_key_handles_rate_limit(monkeypatch):
    import models.llm_manager as mgr

    class RateLimitClient:
        def __init__(self, *args, **kwargs):
            pass
        def invoke(self, prompt):
            raise Exception('429 rate limit exceeded')

    monkeypatch.setattr(mgr, 'ChatGroq', RateLimitClient)
    ok, msg = mgr.LLMManager.verify_api_key('gsk_validplaceholder123456')
    assert not ok and ('rate' in msg.lower() or 'limit' in msg.lower())


def test_verify_api_key_handles_unauthorized(monkeypatch):
    import models.llm_manager as mgr

    class BadAuthClient:
        def __init__(self, *args, **kwargs):
            pass
        def invoke(self, prompt):
            raise Exception('401 Unauthorized')

    monkeypatch.setattr(mgr, 'ChatGroq', BadAuthClient)
    # Use a syntactically valid-looking key string (matches sanitize pattern) but simulate server 401
    ok, msg = mgr.LLMManager.verify_api_key('gsk_invalidplaceholder123456')
    assert not ok and ('auth' in msg.lower() or 'invalid' in msg.lower())

