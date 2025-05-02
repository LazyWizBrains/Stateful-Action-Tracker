#!/usr/bin/env python3

import argparse
import sys
import os
from typing import List, Dict, Any

# Ensure the src directory is in the Python path
# This allows running the script from the project root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 	'.	')))

# Import agent components from the src directory
from src import config
from src import memory_manager
from src import llm_interaction
from src import action_item_parser

# Load environment variables (e.g., API keys)
from dotenv import load_dotenv
load_dotenv()

def get_input_text(input_source: str) -> str:
    """Reads input text from a file or returns the string directly."""
    if os.path.isfile(input_source):
        try:
            with open(input_source, 	'r	', encoding=	'utf-8	') as f:
                print(f"Reading input from file: {input_source}")
                return f.read()
        except IOError as e:
            print(f"Error reading file {input_source}: {e}")
            sys.exit(1)
    else:
        print("Using provided text as input.")
        return input_source

def main():
    parser = argparse.ArgumentParser(description="Stateful Project Action Item Tracker Agent")
    parser.add_argument("-p", "--project", required=True, help="Project ID (used for storing/retrieving action items)")
    parser.add_argument("-i", "--input", required=True, help="Input text containing meeting notes or discussion (can be a string or a path to a text file)")
    parser.add_argument("-s", "--summarize", action="store_true", help="After processing input, generate and print a summary of all action items for the project.")
    parser.add_argument("--force-reparse", action="store_true", help="Force LLM call even if input is empty (for testing prompts).")

    args = parser.parse_args()

    project_id = args.project
    input_source = args.input
    should_summarize = args.summarize

    print(f"--- Starting Action Item Tracker for Project: {project_id} ---")

    # 1. Load existing action items
    all_action_items = memory_manager.load_action_items(project_id)

    # 2. Get input text
    meeting_notes = get_input_text(input_source)

    if not meeting_notes and not args.force_reparse:
        print("Input text is empty. No new information to process.")
    else:
        # 3. Filter for open items to provide context
        open_items = [item for item in all_action_items if item.get(	'status	') == 	'Open	' or item.get(	'status	') == 	'In Progress	']
        print(f"Providing {len(open_items)} open/in-progress items as context to LLM.")

        # 4. Construct the identification prompt
        id_messages = llm_interaction.construct_identification_prompt(project_id, open_items, meeting_notes)

        # 5. Call the LLM
        llm_response_content = llm_interaction.generate_llm_response(id_messages, expect_json=True)

        if llm_response_content:
            # 6. Parse the LLM's JSON response
            parsed_llm_items = action_item_parser.parse_llm_json_response(llm_response_content)

            if parsed_llm_items is not None: # Check if parsing was successful (even if list is empty)
                # 7. Process parsed items (update existing, create new)
                all_action_items = action_item_parser.process_parsed_items(
                    project_id=project_id,
                    parsed_items=parsed_llm_items,
                    existing_items=all_action_items
                )

                # 8. Save the updated list of action items
                save_success = memory_manager.save_action_items(project_id, all_action_items)
                if not save_success:
                    print("Error: Failed to save updated action items.")
                else:
                    print("Successfully saved updated action items.")
            else:
                print("Could not parse a valid list of action items from the LLM response. No changes saved.")
                print("LLM Raw Response:", llm_response_content) # Show raw response for debugging
        else:
            print("Did not receive a valid response from the LLM. No changes made.")

    # 9. Optional: Generate and print summary
    if should_summarize:
        print("\n--- Generating Project Summary ---")
        if not all_action_items:
            print("No action items found for this project to summarize.")
        else:
            summary_messages = llm_interaction.construct_summary_prompt(project_id, all_action_items)
            summary_response = llm_interaction.generate_llm_response(summary_messages)
            if summary_response:
                print("\nProject Summary:")
                print(summary_response)
            else:
                print("Failed to generate summary from LLM.")

    print(f"\n--- Action Item Tracker Finished for Project: {project_id} ---")

if __name__ == "__main__":
    # Check if API key is likely set (basic check)
    if not os.getenv("OPENAI_API_KEY") and "openai" in config.LLM_MODEL.lower():
         print("Warning: OPENAI_API_KEY environment variable not set.")
         print("Please set your API key in a .env file or as an environment variable.")
         # Depending on strictness, you might want to sys.exit(1) here
    # Add checks for other providers based on config.LLM_MODEL if needed
    
    main()


