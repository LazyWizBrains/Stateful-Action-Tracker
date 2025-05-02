import json
import os
from typing import List, Dict, Any, Optional

from .config import ACTION_ITEM_DIR
from .data_structures import ActionItemStatus # Import status type if needed for validation

def get_project_file_path(project_id: str) -> str:
    """Constructs the full path for a project's action item JSON file."""
    # Basic sanitization to prevent directory traversal or invalid filenames
    safe_project_id = "".join(c for c in project_id if c.isalnum() or c in ('_', '-'))
    if not safe_project_id:
        safe_project_id = "default_project"
    filename = f"{safe_project_id}.json"
    return os.path.join(ACTION_ITEM_DIR, filename)

def load_action_items(project_id: str) -> List[Dict[str, Any]]:
    """Loads action items for a given project_id from its JSON file."""
    file_path = get_project_file_path(project_id)
    if not os.path.exists(file_path):
        print(f"No existing data file found for project 	'{project_id}	'. Returning empty list.")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                # Optional: Add validation here to ensure items match expected structure
                print(f"Loaded {len(data)} action items for project 	'{project_id}	'.")
                return data
            else:
                print(f"Warning: Data in {file_path} is not a list. Returning empty list.")
                return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}. Returning empty list.")
        return []
    except IOError as e:
        print(f"Error reading file {file_path}: {e}. Returning empty list.")
        return []

def save_action_items(project_id: str, action_items: List[Dict[str, Any]]) -> bool:
    """Saves the list of action items for a project_id to its JSON file."""
    file_path = get_project_file_path(project_id)

    # Ensure the directory exists (config.py tries, but double-check)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    except OSError as e:
        print(f"Error ensuring directory exists for {file_path}: {e}")
        return False

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(action_items, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(action_items)} action items for project 	'{project_id}	' to {file_path}.")
        return True
    except IOError as e:
        print(f"Error writing file {file_path}: {e}")
        return False
    except TypeError as e:
        print(f"Error serializing action items to JSON: {e}")
        return False

# Example Usage (can be removed or kept for testing)
if __name__ == "__main__":
    from data_structures import create_action_item # Relative import needs adjustment if run directly

    test_project = "TestProject_123"
    items = load_action_items(test_project) # Should be empty initially
    print(f"Initial items for {test_project}: {items}")

    item1 = create_action_item(test_project, "Task 1", owner="Charlie")
    item2 = create_action_item(test_project, "Task 2", status="In Progress")
    items.append(item1)
    items.append(item2)

    success = save_action_items(test_project, items)
    print(f"Save successful: {success}")

    if success:
        loaded_items = load_action_items(test_project)
        print(f"\nLoaded items after save for {test_project}:")
        print(json.dumps(loaded_items, indent=2))

        # Clean up test file
        try:
            test_file_path = get_project_file_path(test_project)
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                print(f"\nCleaned up test file: {test_file_path}")
        except OSError as e:
            print(f"Error cleaning up test file: {e}")


