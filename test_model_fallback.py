
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from models.llm_manager import LLMManager

def test_fallback_initialization():
    print("Testing LLMManager initialization with fallback...")
    try:
        # Get the LLM instance
        llm = LLMManager.get_llm('conversation')
        
        # Verify it's a RunnableWithFallbacks
        print(f"LLM type: {type(llm)}")
        
        # Simple invocation to ensure it works
        print("Invoking model...")
        response = llm.invoke("Hello, are you online?")
        print(f"Response: {response.content}")
        print("✅ Test Passed: Model initialized and invoked successfully.")
        
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fallback_initialization()
