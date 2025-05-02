import json
from typing import List, Dict, Any, Optional

# Use absolute import based on the project structure
from litellm import completion, acompletion, ModelResponse, Choices, Message
import litellm

# Import config variables
from .config import LLM_MODEL

# Optional: Set debug level for litellm
# litellm.set_verbose = True

def construct_system_prompt() -> str:
    """Constructs the system prompt for the action item tracker agent."""
    return (
        "You are an AI assistant specializing in tracking project action items from meeting notes or discussions. "
        "Your capabilities include: identifying new action items (task description, owner, deadline), tracking their status (Open, In Progress, Completed, Cancelled), "
        "and updating existing items based on new information. Always associate items with the current project context. "
        "When identifying or updating action items based on meeting notes, respond ONLY with a valid JSON list containing the action item objects (new or updated). "
        "Each object must conform to the specified structure. If no new items or updates are found, respond with an empty JSON list []. "
        "For other tasks like summarization or general queries, respond in clear, concise natural language. "
        "You will be provided with the current meeting notes/input and a list of currently open action items for context." 
        "Ensure generated/updated action items have unique IDs (you can reuse existing IDs for updates, but generate new UUIDs for new items if asked, otherwise the calling code handles ID generation)."
        "Focus on extracting information explicitly mentioned or strongly implied in the text."
    )

def construct_identification_prompt(
    project_id: str,
    open_items: List[Dict[str, Any]],
    meeting_notes: str
) -> List[Dict[str, str]]:
    """Constructs the messages list for identifying/updating action items."""
    system_message = construct_system_prompt()
    
    open_items_json = json.dumps(open_items, indent=2) if open_items else "None"
    
    user_prompt = (
        f"Current Project: {project_id}\n\n"
        f"Currently Open Action Items:\n{open_items_json}\n\n"
        f"Meeting Notes/Input:\n"""\n{meeting_notes}\n"""\n\n"
        f"Analyze the notes. Identify any new action items mentioned. Check if any open items listed above are discussed or updated (e.g., marked as done, progress mentioned, owner assigned/changed). "
        f"Respond ONLY with a JSON list containing objects for new action items or existing items that need updates based *only* on the provided notes. "
        f"For updated items, include their existing \'id\'. For new items, omit the \'id\' field (it will be generated later). "
        f"Ensure the response is *only* the JSON list, nothing else before or after. If no items are found or updated, return an empty list []."
    )
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]
    return messages

def construct_summary_prompt(
    project_id: str,
    all_items: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Constructs the messages list for requesting an action item summary."""
    system_message = construct_system_prompt()
    
    all_items_json = json.dumps(all_items, indent=2) if all_items else "None"
    
    user_prompt = (
        f"Current Project: {project_id}\n\n"
        f"All Action Items:\n{all_items_json}\n\n"
        f"Provide a concise summary of the action items for this project. Group them by status (Open, In Progress, Completed, Cancelled)."
    )
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]
    return messages

def generate_llm_response(messages: List[Dict[str, str]], expect_json: bool = False) -> Optional[str]:
    """Calls the LLM using LiteLLM and returns the response content."""
    try:
        print(f"\n--- Sending request to LLM ({LLM_MODEL}) ---")
        # print("Messages:", json.dumps(messages, indent=2))
        
        response: ModelResponse = completion(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=2048, # Adjust as needed
            temperature=0.2, # Lower temperature for more deterministic JSON output
            # Add response_format for providers that support it (like OpenAI)
            # response_format={"type": "json_object"} if expect_json else None 
            # Note: LiteLLM might not universally support response_format yet, 
            # relying on prompt instructions is safer for broader compatibility.
        )
        
        print("--- LLM Response Received ---")
        
        if response and response.choices and response.choices[0].message and response.choices[0].message.content:
            content = response.choices[0].message.content.strip()
            # print("Raw Content:", content)
            return content
        else:
            print("Error: Received an empty or invalid response from LLM.")
            print("Full Response Object:", response)
            return None
            
    except Exception as e:
        print(f"Error calling LLM via LiteLLM: {e}")
        # Consider more specific error handling based on LiteLLM exceptions if available
        return None

# Example Usage (can be removed or kept for testing)
if __name__ == "__main__":
    # Ensure you have a .env file with your API key (e.g., OPENAI_API_KEY)
    # Or set the environment variable directly
    from dotenv import load_dotenv
    load_dotenv()
    import os
    if not os.getenv("OPENAI_API_KEY"):
         print("Please set your OPENAI_API_KEY in a .env file or environment variable to run this example.")
    else:
        print("Testing LLM Interaction...")
        test_project = "LLM_Test_Project"
        test_notes = """
        Meeting Notes - May 2, 2025
        Attendees: Alice, Bob, Charlie
        
        Discussion Points:
        - Alice needs to finalize the report by next Friday.
        - Bob mentioned the server migration is ongoing, should be done by EOD tomorrow.
        - We need someone to schedule the follow-up meeting. Charlie volunteers.
        - The previous action item for Dave (ID: xyz-123) about updating the docs is complete.
        """
        test_open_items = [
            {
                "id": "abc-789",
                "project_id": test_project,
                "task": "Review budget proposal",
                "owner": "Alice",
                "deadline": "2025-05-05",
                "status": "Open",
                "created_at": "2025-04-28T10:00:00Z",
                "updated_at": "2025-04-28T10:00:00Z",
                "source_meeting": "Meeting 1",
                "update_history": []
            },
            {
                "id": "xyz-123",
                "project_id": test_project,
                "task": "Update the user documentation",
                "owner": "Dave",
                "deadline": None,
                "status": "In Progress",
                "created_at": "2025-04-20T11:00:00Z",
                "updated_at": "2025-04-25T15:30:00Z",
                "source_meeting": "Meeting 0",
                "update_history": [{"timestamp": "2025-04-25T15:30:00Z", "changes": "Changed status from Open to In Progress"}]
            }
        ]

        # Test Identification/Update Prompt
        print("\n--- Testing Identification/Update ---")
        id_messages = construct_identification_prompt(test_project, test_open_items, test_notes)
        id_response = generate_llm_response(id_messages, expect_json=True)
        print("\nIdentification Response (JSON expected):")
        print(id_response)

        # Test Summary Prompt
        print("\n--- Testing Summary ---")
        # Combine open and potentially updated items for summary test
        all_test_items = test_open_items # In reality, merge results from id_response here
        summary_messages = construct_summary_prompt(test_project, all_test_items)
        summary_response = generate_llm_response(summary_messages)
        print("\nSummary Response (Text expected):")
        print(summary_response)


