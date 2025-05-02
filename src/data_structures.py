import uuid
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any

# Define the possible statuses for an action item
ActionItemStatus = Literal["Open", "In Progress", "Completed", "Cancelled"]

# Using a dictionary structure as defined in the design document.
# Using TypedDict or Pydantic could offer more robustness, but a dict is simpler for this example.

def create_action_item(
    project_id: str,
    task: str,
    owner: Optional[str] = None,
    deadline: Optional[str] = None,
    status: ActionItemStatus = "Open",
    source_meeting: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new action item dictionary with default values."""
    now = datetime.utcnow().isoformat() + "Z" # ISO 8601 format with Z for UTC
    return {
        "id": str(uuid.uuid4()), # Generate a unique ID
        "project_id": project_id,
        "task": task,
        "owner": owner,
        "deadline": deadline,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "source_meeting": source_meeting,
        "update_history": [] # Initialize empty history
    }

def update_action_item(
    item: Dict[str, Any],
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Updates an existing action item dictionary and adds history."""
    now = datetime.utcnow().isoformat() + "Z"
    change_log = []

    for key, value in updates.items():
        if key in item and item[key] != value:
            change_log.append(f"Changed 	'{key}	' from 	'{item[key]}	' to 	'{value}	'")
            item[key] = value
        elif key not in item:
            # Handle adding new fields if necessary, though typically we update existing ones
            change_log.append(f"Added 	'{key}	' with value 	'{value}	'")
            item[key] = value

    if change_log:
        item["updated_at"] = now
        history_entry = {
            "timestamp": now,
            "changes": "; ".join(change_log)
        }
        if "update_history" not in item or not isinstance(item["update_history"], list):
            item["update_history"] = []
        item["update_history"].append(history_entry)

    # Ensure status is valid if updated
    if "status" in updates and updates["status"] not in ["Open", "In Progress", "Completed", "Cancelled"]:
        print(f"Warning: Invalid status 	'{updates['status']}	' provided for item {item.get('id')}. Keeping previous status 	'{item.get('status')}	'.")
        # Revert status if invalid - find the original status before this update batch
        original_status = item.get("status") # Default to current if history is complex
        for change in reversed(change_log):
             if change.startswith("Changed 	'status	'"):
                 parts = change.split(" from 	'")
                 if len(parts) > 1:
                     original_status = parts[1].split("\t' to")[0]
                     break
        item["status"] = original_status


    return item

# Example Usage (can be removed or kept for testing)
if __name__ == "__main__":
    project1 = "ProjectAlpha"
    item1 = create_action_item(project1, "Setup initial repository", owner="Alice")
    print("Created Item:")
    import json
    print(json.dumps(item1, indent=2))

    updates = {"status": "In Progress", "owner": "Bob"}
    item1 = update_action_item(item1, updates)
    print("\nUpdated Item:")
    print(json.dumps(item1, indent=2))

    updates2 = {"status": "Completed", "deadline": "2025-05-10"}
    item1 = update_action_item(item1, updates2)
    print("\nUpdated Item Again:")
    print(json.dumps(item1, indent=2))

    # Test invalid status
    updates_invalid = {"status": "Done"}
    item1 = update_action_item(item1, updates_invalid)
    print("\nAttempted Invalid Update:")
    print(json.dumps(item1, indent=2))


