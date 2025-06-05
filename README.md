# Petri Net Data Synthesis from Multimedia Scenarios

This project focuses on generating, validating, and visualizing Petri net data structures from textual descriptions of multimedia scenarios. It leverages a Large Language Model (LLM) for synthesizing new data pairs (scenario text and corresponding Petri net JSON) and provides tools for managing and inspecting these datasets.

## Overview

-   **Input:**
    -   Textual descriptions of multimedia scenarios.
    -   Hand-made examples of (scenario text, Petri net JSON) pairs.
-   **Core Processes:**
    -   **Data Synthesis:**
        -   Paraphrasing existing scenario descriptions while preserving their Petri net structure.
        -   Forward generation of novel scenario texts and their corresponding Petri net JSON using an LLM.
    -   **Validation:**
        -   Structural validation of generated Petri net JSON against a defined schema.
        -   Logical consistency checks on the Petri net structure (e.g., arc validity, node connectivity).
    -   **Visualization:**
        -   Generation of PDF visual representations of Petri nets from their JSON data.
-   **Output:**
    -   Structured JSON files representing Petri nets (places, transitions, arcs, initial marking).
    -   Text files containing the scenario descriptions.
    -   PDF visualizations of the Petri nets.
    -   Organized directories for hand-made data, synthesized data (approved, manually rejected, auto-rejected).

## Features

*   **LLM-Powered Data Synthesis:** Uses Google's Gemini model to generate new scenario descriptions and Petri net JSON.
*   **Paraphrasing:** Creates variations of existing scenario texts.
*   **Forward Generation:** Generates entirely new (text, Petri net JSON) pairs, involving a manual review step.
*   **Schema and Logic Validation:** Ensures generated Petri nets adhere to a predefined JSON schema ([schemas/petri_net_schema.json](schemas/petri_net_schema.json)) and logical rules.
*   **PDF Visualization:** Converts Petri net JSON into human-readable PDF diagrams using Graphviz.
*   **Command-Line Interface:** Provides tools for data synthesis, validation, and visualization via `src/main.py`.
*   **Organized Data Management:** Systematically stores input data, generated outputs, and intermediate files.

## Technology Stack

*   Python 3.x
*   Google Generative AI SDK (`google-generativeai`) for LLM interaction.
*   `jsonschema` for validating Petri net JSON structures.
*   `graphviz` for rendering Petri net visualizations.
*   `python-dotenv` for managing API keys and configurations.

## Project Structure

```
.
├── .env                  # Environment variables (e.g., API keys)
├── .gitignore            # Specifies intentionally untracked files
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── data/                 # Input data, including hand-made samples
│   ├── 01/
│   ├── ...
│   └── hand_made/
├── outputs/              # All generated files
│   ├── review_temp/      # Temporary files for manual review
│   └── synthesized_data/ # Persisted synthesized data
│       ├── approved/
│       ├── invalid_auto_rejected/
│       └── rejected_manual/
├── schemas/
│   └── petri_net_schema.json # JSON schema for Petri net data
└── src/                  # Source code
    ├── __init__.py
    ├── config.py         # Configuration settings and paths
    ├── data_synthesis.py # Logic for LLM-based data generation
    ├── llm_interaction.py  # Interface for communicating with the LLM
    ├── main.py           # Command-line interface entry point
    ├── petri_net_utils.py  # Utilities for Petri net visualization
    └── validation.py     # Petri net validation logic
```

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Graphviz:**
    Graphviz is required for visualizing Petri nets. Download and install it from [graphviz.org](https://graphviz.org/download/). Ensure the Graphviz `bin` directory is added to your system's PATH environment variable.

5.  **Set up Environment Variables:**
    Create a `.env` file in the project root directory by copying the example or creating a new one:
    ```env
    # .env
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
    ```
    Replace `"YOUR_GOOGLE_API_KEY_HERE"` with your actual Google API key for the Gemini model.

## Usage (Command-Line Interface)

The main interaction with the project is through `src/main.py`.

```bash
python src/main.py <action> [options]
```

**Available Actions:**

1.  **`paraphrase`**: Generate paraphrased versions of a hand-made scenario text.
    *   `--sample_id <id>`: (Required) ID of the hand-made sample (e.g., `sample_01` from `data/hand_made/`).
    *   `--num_paraphrases <N>`: Number of paraphrases to generate (default: 3).
    *Example:*
    ```bash
    python src/main.py paraphrase --sample_id sample_01 --num_paraphrases 2
    ```

2.  **`forward_gen`**: Generate new (scenario text, Petri net JSON) pairs using the LLM. This involves a manual review step.
    *   `--num_forward_samples <N>`: Number of new pairs to generate (default: 1).
    *   `--num_few_shot <N>`: Number of hand-made examples to use for few-shot prompting (default: 2).
    *Example:*
    ```bash
    python src/main.py forward_gen --num_forward_samples 1 --num_few_shot 3
    ```
    During this process, candidates are saved in `outputs/review_temp/`. You will be prompted in the console to approve or reject each candidate.

3.  **`validate_sample`**: Validate an existing Petri net JSON file.
    *   `--sample_id <id>`: (Required) Stem of the sample file.
        *   For hand-made: e.g., `sample_01`.
        *   For synthesized: e.g., `gen_approved_abcdef12`.
    *   `--data_type <type>`: (Required) Choices: `hand_made`, `synthesized`.
    *Example:*
    ```bash
    python src/main.py validate_sample --sample_id gen_approved_2898622b --data_type synthesized
    python src/main.py validate_sample --sample_id sample_01 --data_type hand_made
    ```

4.  **`visualize_sample`**: Generate a new PDF visualization for an existing sample.
    *   `--sample_id <id>`: (Required) Stem of the sample file (same as for `validate_sample`).
    *   `--data_type <type>`: (Required) Choices: `hand_made`, `synthesized`.
    *The visualization will be saved in `outputs/review_temp/` with an `_adhoc_viz` suffix.*
    *Example:*
    ```bash
    python src/main.py visualize_sample --sample_id gen_approved_2898622b --data_type synthesized
    ```

## Workflow for Forward Generation

1.  **Prompting:** Few-shot examples from `data/hand_made/` are used to construct a prompt for the LLM.
2.  **LLM Generation:** The LLM generates a candidate scenario text and its corresponding Petri net JSON.
3.  **Structural Validation:** The generated JSON is validated against the schema in `schemas/petri_net_schema.json` and undergoes logical checks (see `src/validation.py`).
    *   If invalid, the sample is saved to `outputs/synthesized_data/invalid_auto_rejected/` and the process may continue with the next candidate.
4.  **Temporary Storage & Review:** Valid candidates are saved to `outputs/review_temp/` along with a PDF visualization.
5.  **Manual Review:** The user is prompted in the console to review the text, JSON, and PDF.
    *   **Approve:** The sample (text, JSON, PDF) is moved to a new numbered subfolder in `outputs/synthesized_data/approved/`.
    *   **Reject:** The sample (text, JSON) is moved to `outputs/synthesized_data/rejected_manual/`. A PDF is *not* typically saved here unless generated ad-hoc.
6.  **Cleanup:** Temporary files for the reviewed candidate are removed from `outputs/review_temp/`.

## Data Format

*   **Scenario Text:** Plain text files (`.txt`) describing a multimedia interaction or process.
*   **Petri Net JSON:** JSON files (`.json`) structured according to [schemas/petri_net_schema.json](schemas/petri_net_schema.json). Key components include:
    *   `places`: An object mapping place IDs to descriptive labels.
    *   `transitions`: An object mapping transition IDs to descriptive labels.
    *   `arcs`: An array of objects, each defining a directed connection (`from` node ID, `to` node ID).
    *   `initial`: An object mapping place IDs to their initial token count (must be >= 1).

## Acknowledgments
*   Google for the Gemini Pro API.
*   The creators of Graphviz and `jsonschema`.