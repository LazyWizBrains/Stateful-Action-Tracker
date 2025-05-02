import json
from typing import List, Dict, Any, Optional

from .data_structures import create_action_item, update_action_item, ActionItemStatus

def parse_llm_json_response(response_content: str) -> Optional[List[Dict[str, Any]]]:
    """Parses the LLM response string, expecting a JSON list of action items."""
    if not response_content:
        print("Parser received empty response content.")
        return None

    # Sometimes the LLM might still wrap the JSON in backticks or add commentary
    # Try to extract the JSON part more robustly
    json_start = response_content.find("[")
    json_end = response_content.rfind("]")

    if json_start == -1 or json_end == -1 or json_end < json_start:
        print(f"Parser could not find valid JSON list structure in response: {response_content[:200]}...")
        # Attempt to see if it's a single object instead of a list
        json_start_obj = response_content.find("{")
        json_end_obj = response_content.rfind("}")
        if json_start_obj != -1 and json_end_obj != -1 and json_end_obj > json_start_obj:
             potential_json = response_content[json_start_obj : json_end_obj + 1]
             try:
                 parsed_obj = json.loads(potential_json)
                 if isinstance(parsed_obj, dict):
                     print("Parser found a single JSON object, wrapping it in a list.")
                     return [parsed_obj] # Return as a list containing the single object
                 else:
                     print(f"Parser found JSON, but it wasn\t a dictionary: {type(parsed_obj)}")
                     return None
             except json.JSONDecodeError as e:
                 print(f"Parser failed to decode potential single object JSON: {e}")
                 print(f"Content snippet: {potential_json[:200]}...")
                 return None
        else:
            return None # Neither list nor object structure found

    potential_json_list = response_content[json_start : json_end + 1]

    try:
        parsed_data = json.loads(potential_json_list)
        if isinstance(parsed_data, list):
            # Optional: Add validation for each item in the list here
            print(f"Parser successfully decoded JSON list with {len(parsed_data)} items.")
            return parsed_data
        else:
            print(f"Parser decoded JSON, but it was not a list: {type(parsed_data)}")
            return None
    except json.JSONDecodeError as e:
        print(f"Parser failed to decode JSON list: {e}")
        print(f"Content snippet: {potential_json_list[:200]}...")
        # Fallback: Maybe the LLM ignored instructions and just gave text?
        # Handle this case if necessary, e.g., by trying another LLM call asking for JSON.
        return None

def process_parsed_items(
    project_id: str,
    parsed_items: List[Dict[str, Any]],
    existing_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Processes items from LLM, creating new ones or updating existing ones."""
    updated_item_ids = set()
    newly_created_items = []
    existing_items_map = {item["id"]: item for item in existing_items}

    print(f"Processing {len(parsed_items)} items received from LLM.")

    for llm_item in parsed_items:
        item_id = llm_item.get("id")

        if item_id and item_id in existing_items_map:
            # This is an update to an existing item
            existing_item = existing_items_map[item_id]
            print(f"Updating existing item ID: {item_id}")
            # Prepare updates, excluding immutable fields like id, project_id, created_at
            updates = {k: v for k, v in llm_item.items() if k not in ["id", "project_id", "created_at", "update_history"]}
            update_action_item(existing_item, updates)
            updated_item_ids.add(item_id)
        elif "task" in llm_item: # Check if it looks like a valid new item (must have a task)
            # This is potentially a new item (LLM was asked to omit ID for new items)
            print(f"Creating new item for task: {llm_item.get(	'task	')[:50]}...")
            # Extract details provided by LLM
            new_item = create_action_item(
                project_id=project_id,
                task=llm_item["task"],
                owner=llm_item.get("owner"),
                deadline=llm_item.get("deadline"),
                status=llm_item.get("status", "Open"), # Default to Open if not specified
                source_meeting="LLM Extraction" # Indicate source
            )
            # Validate status if provided by LLM
            if "status" in llm_item and llm_item["status"] not in ["Open", "In Progress", "Completed", "Cancelled"]:
                print(f"Warning: LLM provided invalid status 	'{llm_item['status']}	' for new item. Defaulting to 	'Open	'.")
                new_item["status"] = "Open"
            
            newly_created_items.append(new_item)
        else:
            print(f"Warning: Parsed item ignored - missing 	'task	' or invalid structure: {llm_item}")

    # Combine existing items (updated or untouched) with newly created items
    final_item_list = []
    for item in existing_items:
        final_item_list.append(item) # Add updated or untouched existing items
    
    final_item_list.extend(newly_created_items) # Add the new items

    print(f"Processing complete. Total items: {len(final_item_list)}. Updated: {len(updated_item_ids)}. Created: {len(newly_created_items)}.")
    return final_item_list

# Example Usage (can be removed or kept for testing)
if __name__ == "__main__":
    test_json_response_ok = """ 
    [
      {
        "task": "Finalize the report",
        "owner": "Alice",
        "deadline": "next Friday"
      },
      {
        "id": "xyz-123", 
        "status": "Completed"
      },
      {
        "task": "Schedule follow-up meeting",
        "owner": "Charlie",
        "status": "Open"
      }
    ]
    """
    
    test_json_response_empty = "[]"
    test_json_response_bad = "Here is the JSON: {\"task\": \"Fail\"}"
    test_json_response_single_obj = "```json\n{\"task\": \"Single Task\", \"owner\": \"Me\"}\n```"

    print("--- Testing Parser --- ")
    parsed_ok = parse_llm_json_response(test_json_response_ok)
    print("Parsed OK:", json.dumps(parsed_ok, indent=2) if parsed_ok else "None")
    
    parsed_empty = parse_llm_json_response(test_json_response_empty)
    print("Parsed Empty:", parsed_empty)
    
    parsed_bad = parse_llm_json_response(test_json_response_bad)
    print("Parsed Bad:", parsed_bad)

    parsed_single = parse_llm_json_response(test_json_response_single_obj)
    print("Parsed Single Obj:", json.dumps(parsed_single, indent=2) if parsed_single else "None")

    print("\n--- Testing Processor --- ")
    existing = [
        {
            "id": "xyz-123",
            "project_id": "TestProc",
            "task": "Update docs",
            "owner": "Dave",
            "status": "In Progress",
            "created_at": "2025-04-20T11:00:00Z",
            "updated_at": "2025-04-25T15:30:00Z",
            "update_history": []
        }
    ]
    
    if parsed_ok:
        final_list = process_parsed_items("TestProc", parsed_ok, existing)
        print("\nFinal Processed List:")
        print(json.dumps(final_list, indent=2))
    else:
        print("Skipping processor test as parsing failed.")


