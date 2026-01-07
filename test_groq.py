
try:
    from langchain_groq import ChatGroq
    print("Import ChatGroq successful")
    try:
        llm = ChatGroq(api_key="gsk_fake", model_name="llama3-8b-8192")
        print("Instantiate ChatGroq successful")
    except Exception as e:
        print(f"Instantiate ChatGroq failed: {e}")

except ImportError as e:
    print(f"Import ChatGroq failed: {e}")
except Exception as e:
    print(f"Other error: {e}")
