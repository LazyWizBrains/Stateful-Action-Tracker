# Stateful Project Action Item Tracker AI Agent

## Overview

This project implements an AI agent designed to track action items for specific projects across multiple interactions or meeting notes. It leverages Large Language Models (LLMs) through the `litellm` library to understand natural language input (like meeting transcripts), identify new action items, and update the status of existing ones. The agent maintains the state of action items persistently, providing a memory of tasks associated with a project.

## Features

*   **Project-Based Tracking:** Action items are associated with specific project IDs.
*   **Action Item Identification:** Uses an LLM to parse input text (meeting notes, discussions) and extract potential action items (task, owner, deadline).
*   **Stateful Memory:** Persistently stores action items in JSON files (one per project), allowing tracking across multiple sessions.
*   **Contextual Updates:** Provides the LLM with context about existing open/in-progress items to facilitate status updates (e.g., marking items as completed).
*   **Summarization:** Can generate a summary of all action items for a project, grouped by status.
*   **LLM Agnostic (via LiteLLM):** Designed to work with various LLMs supported by `litellm` (tested primarily with OpenAI models like GPT-4o-mini).

## Project Structure

```
/action_tracker_agent
|-- .env                 # For storing API keys (MUST BE CREATED)
|-- main_agent_loop.py   # Main executable script for the agent
|-- requirements.txt     # Python dependencies
|-- project_data/        # Directory to store project action item JSON files (created automatically)
|   `-- <project_id>.json # Example data file
|-- src/
|   |-- __init__.py
|   |-- config.py          # Loads configuration (LLM model, storage path)
|   |-- data_structures.py # Defines action item structure and helper functions
|   |-- memory_manager.py  # Handles loading/saving action items from/to JSON files
|   |-- llm_interaction.py # Manages prompt construction and communication with the LLM via litellm
|   `-- action_item_parser.py # Parses JSON responses from the LLM and processes items
|-- README.md            # This file
|-- README_hr.md         # Code explanation in Croatian (to be created)
`-- github_instructions.md # Instructions for pushing to GitHub (to be created)
```

## Setup

1.  **Clone the Repository (or create files):** Obtain the project files.

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Key:**
    *   Create a file named `.env` in the `action_tracker_agent` root directory.
    *   Add your LLM provider's API key to the `.env` file. For example, if using OpenAI:
        ```
        OPENAI_API_KEY="your_actual_openai_api_key_here"
        ```
    *   Replace `"your_actual_openai_api_key_here"` with your real key.
    *   If you want to use a different LLM model supported by `litellm`, you can also set the `LLM_MODEL` environment variable in the `.env` file (e.g., `LLM_MODEL="anthropic/claude-3-haiku-20240307"`) and ensure the corresponding API key (e.g., `ANTHROPIC_API_KEY`) is also set.

## Usage

The agent is run from the command line using `main_agent_loop.py`.

**Basic Syntax:**

```bash
python main_agent_loop.py -p <project_id> -i <input_source> [-s]
```

**Arguments:**

*   `-p` or `--project` (Required): A unique identifier for the project you want to track action items for (e.g., `"ProjectAlpha"`, `"WebsiteRedesign"`). This determines which JSON file (`project_data/<project_id>.json`) is used for storage.
*   `-i` or `--input` (Required): The source of the text to be processed. This can be:
    *   A string containing the meeting notes or discussion directly.
    *   The path to a text file (`.txt`) containing the notes.
*   `-s` or `--summarize` (Optional): If included, the agent will print a summary of all action items for the specified project after processing the input.

**Examples:**

1.  **Process notes from a file and save updates:**
    ```bash
    # Assuming you have notes in a file named meeting_notes.txt
    echo "Alice to send the slides by Friday. Bob confirmed the deployment is done (ref item xyz-123). Need to define API spec." > meeting_notes.txt
    
    python main_agent_loop.py -p "ProjectX" -i meeting_notes.txt 
    ```
    *This will load existing items for `ProjectX`, process `meeting_notes.txt`, identify new items (e.g., "send slides", "define API spec"), update existing items (e.g., mark `xyz-123` as completed if found), and save the results back to `project_data/ProjectX.json`.*

2.  **Process notes directly from a string and request a summary:**
    ```bash
    python main_agent_loop.py -p "ProjectY" -i "Charlie will investigate the login bug. The budget was approved." -s
    ```
    *This will process the input string for `ProjectY`, save any identified items/updates, and then print a summary of all items currently stored for `ProjectY`.*

3.  **Run summary only (process empty input):**
    ```bash
    # Use an empty string or non-existent file path for input if you only want the summary
    python main_agent_loop.py -p "ProjectX" -i "" -s 
    ```
    *This loads items for `ProjectX` and immediately generates a summary without processing new notes.*

## Code Explanation

*   **`main_agent_loop.py`:**
    *   Parses command-line arguments (`argparse`).
    *   Loads the API keys and configuration using `dotenv` and `src/config.py`.
    *   Calls `memory_manager.load_action_items` to get the current state for the project.
    *   Reads the input text from the specified source.
    *   Filters the loaded items to find currently open/in-progress ones to provide context to the LLM.
    *   Calls `llm_interaction.construct_identification_prompt` to create the prompt messages.
    *   Calls `llm_interaction.generate_llm_response` to interact with the LLM via `litellm`.
    *   Calls `action_item_parser.parse_llm_json_response` to extract the JSON list from the LLM's response.
    *   Calls `action_item_parser.process_parsed_items` to merge the LLM's findings with the existing items (updating statuses, adding new items).
    *   Calls `memory_manager.save_action_items` to persist the updated list.
    *   Optionally calls the LLM again via `llm_interaction` functions to generate a summary if requested.

*   **`src/config.py`:**
    *   Loads environment variables from the `.env` file.
    *   Defines configuration constants like the `LLM_MODEL` to use (defaulting to `openai/gpt-4o-mini`) and the `ACTION_ITEM_DIR` for storing data.
    *   Creates the `ACTION_ITEM_DIR` if it doesn't exist.
    *   Includes basic checks for the presence of API keys based on the selected model.

*   **`src/data_structures.py`:**
    *   Defines the structure of an action item using a dictionary.
    *   Provides `create_action_item` to initialize a new item with a unique ID (`uuid.uuid4()`) and timestamps.
    *   Provides `update_action_item` to modify an existing item, automatically updating the `updated_at` timestamp and logging changes in `update_history`.

*   **`src/memory_manager.py`:**
    *   `get_project_file_path`: Constructs the path to the JSON file for a given project ID, including basic filename sanitization.
    *   `load_action_items`: Reads and parses the JSON file for a project, returning a list of action item dictionaries. Handles file-not-found and JSON decoding errors.
    *   `save_action_items`: Writes the list of action item dictionaries back to the project's JSON file. Handles file I/O errors.

*   **`src/llm_interaction.py`:**
    *   `construct_system_prompt`: Defines the core instructions for the LLM, telling it its role, capabilities, and required output formats (especially the JSON format for item identification/updates).
    *   `construct_identification_prompt`: Creates the specific prompt for analyzing meeting notes. It includes the project ID, the list of currently open items (as JSON), and the meeting notes, asking the LLM to identify new items or updates and respond *only* with a JSON list.
    *   `construct_summary_prompt`: Creates the prompt for requesting a text summary of all action items for a project.
    *   `generate_llm_response`: The core function for calling the LLM using `litellm.completion`. It sends the constructed messages, specifies the model from `config.py`, and handles potential errors, returning the LLM's response content.

*   **`src/action_item_parser.py`:**
    *   `parse_llm_json_response`: Takes the raw string response from the LLM and attempts to extract a valid JSON list from it. It includes logic to handle cases where the LLM might wrap the JSON in backticks or provide extraneous text.
    *   `process_parsed_items`: Takes the list of items parsed from the LLM response and merges them with the existing list of action items. It checks if an item from the LLM has an ID matching an existing item (indicating an update) or if it's a new item (identified by the presence of a `task` field and absence of a matching ID). It uses `data_structures.create_action_item` and `data_structures.update_action_item` to manage the items correctly.

## Limitations & Future Improvements

*   **Input Format:** Currently assumes plain text input. Could be extended to handle audio files (requiring a transcription step) or calendar integrations.
*   **Error Handling:** Basic error handling is included, but could be made more robust (e.g., retries for LLM calls, more specific exception handling).
*   **LLM Reliability:** The accuracy of action item identification and updates depends heavily on the LLM's ability to follow instructions and interpret the text correctly. The JSON output format constraint helps, but occasional failures might occur.
*   **Complex Updates:** Handling very complex updates (e.g., merging duplicate items, complex dependency tracking) might require more sophisticated logic beyond simple status changes.
*   **User Interface:** Currently CLI-based. A web interface or integration with chat platforms could improve usability.
*   **Concurrency:** The current file-based storage is not suitable for concurrent access by multiple users or processes for the same project.
A database would be needed for multi-user scenarios.

## Licensing & Commercial Use

This project is licensed under a custom license prohibiting commercial use without permission.

For commercial inquiries or licensing requests, please contact me at [damsho992@gmail.com] or [https://github.com/hans992].
