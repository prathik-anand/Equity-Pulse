try:
    from duckduckgo_search import DDGS
    print("Successfully imported DDGS from duckduckgo_search")
    ddgs = DDGS()
    print("Instance created")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
