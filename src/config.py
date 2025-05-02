import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LLM Configuration ---
# Default model, can be overridden if needed
# Ensure the corresponding API key is set in the .env file
# Example: For OpenAI, set OPENAI_API_KEY
# Example: For Anthropic, set ANTHROPIC_API_KEY
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

# --- Storage Configuration ---
# Directory to store project action item files (JSON)
ACTION_ITEM_DIR = os.getenv("ACTION_ITEM_DIR", "/home/ubuntu/action_tracker_agent/project_data")

# Ensure the action item directory exists
if not os.path.exists(ACTION_ITEM_DIR):
    try:
        os.makedirs(ACTION_ITEM_DIR)
        print(f"Created action item storage directory: {ACTION_ITEM_DIR}")
    except OSError as e:
        print(f"Error creating directory {ACTION_ITEM_DIR}: {e}")
        # Depending on requirements, might want to exit or raise exception

# --- API Key Check (Optional but Recommended) ---
# Example check for OpenAI key
if "openai" in LLM_MODEL.lower():
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set. OpenAI models may not work.")
# Add similar checks for other providers if needed

print("Configuration loaded.")
print(f"Using LLM Model: {LLM_MODEL}")
print(f"Action Item Storage: {ACTION_ITEM_DIR}")


