
try:
    import langchain
    print(f"Langchain version: {langchain.__version__}")
    print(f"Langchain file: {langchain.__file__}")
    try:
        from langchain.chains import ConversationChain
        print("Import langchain.chains successful")
    except ImportError as e:
        print(f"Import langchain.chains failed: {e}")

    try:
        from langchain_community.chat_models import ChatGroq
        print("Import langchain_community successful")
    except ImportError as e:
        print(f"Import langchain_community failed: {e}")

except ImportError as e:
    print(f"Import langchain failed: {e}")
