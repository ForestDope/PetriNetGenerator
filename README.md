# Petri Net Data Synthesis from Multimedia Scenarios

This project focuses on generating, validating, and visualizing Petri net data structures from textual descriptions of multimedia scenarios. It leverages a Large Language Model (LLM) for synthesizing new data pairs (scenario text and corresponding Petri net JSON) and provides tools for managing and inspecting these datasets.

## Overview

-   **Input:**
    -   Textual descriptions of multimedia scenarios.
    -   Hand-made examples of (scenario text, Petri net JSON) pairs.
    -   User-provided scenario text for direct generation.
-   **Core Processes:**
    -   **Data Synthesis:**
        -   Paraphrasing existing scenario descriptions while preserving their Petri net structure.
        -   Forward generation of novel scenario texts and their corresponding Petri net JSON using an LLM.
        -   Direct generation of Petri net JSON from user-provided scenario text.
    -   **Validation:**
        -   Structural validation of generated Petri net JSON against a defined schema.
        -   Logical consistency checks on the Petri net structure (e.g., arc validity, node connectivity).
    -   **Visualization:**
        -   Generation of PDF visual representations of Petri nets from their JSON data.
-   **Output:**
    -   Structured JSON files representing Petri nets (places, transitions, arcs, initial marking).
    -   Text files containing the scenario descriptions.
    -   PDF visualizations of the Petri nets.
    -   Organized directories for hand-made data, synthesized data (approved, manually rejected, auto-rejected), and text generated outputs.

## Features

*   **LLM-Powered Data Synthesis:** Uses Google's Gemini model to generate new scenario descriptions and Petri net JSON.
*   **Paraphrasing:** Creates variations of existing scenario texts while preserving their underlying Petri net structure.
*   **Forward Generation:** Generates entirely new (text, Petri net JSON) pairs from scratch, involving a manual review step.
*   **User Text-to-Petri Generation:** Allows users to input scenario text directly and receive corresponding Petri net JSON and PDF visualization.
*   **Schema and Logic Validation:** Ensures generated Petri nets adhere to a predefined JSON schema ([schemas/petri_net_schema.json](schemas/petri_net_schema.json)) and logical rules.
*   **PDF Visualization:** Converts Petri net JSON into human-readable PDF diagrams using Graphviz.
*   **Command-Line Interface:** Provides comprehensive tools for data synthesis, validation, and visualization via `src/main.py`.
*   **Organized Data Management:** Systematically stores input data, generated outputs, and intermediate files in structured directories.
*   **Flexible Few-shot Learning:** Supports configurable few-shot prompting using hand-made examples to improve generation quality.

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
│   ├── generated_from_text/    # Ad-hoc text-to-JSON generation results
│   ├── model_checkpoints/      # Fine-tuning model checkpoints
│   ├── review_temp/            # Temporary files for manual review
│   ├── synthesized_data/       # Persisted synthesized data
│   │   ├── approved/           # Manually approved generated samples
│   │   ├── invalid_auto_rejected/  # Invalid samples auto-rejected
│   │   └── rejected_manual/    # Manually rejected samples
│   ├── train_data/            # Training data for fine-tuning
│   └── val_data/              # Validation data for fine-tuning
├── schemas/
│   └── petri_net_schema.json # JSON schema for Petri net data
└── src/                  # Source code
    ├── __init__.py
    ├── config.py         # Configuration settings and paths
    ├── data_synthesis.py # Logic for LLM-based data generation
    ├── generate_from_text.py # User text-to-JSON generation
    ├── inference.py      # CLI to generate JSON from user-entered scenario text
    ├── llm_interaction.py  # Interface for communicating with the LLM
    ├── main.py           # Command-line interface entry point
    ├── petri_net_utils.py  # Utilities for Petri net visualization
    ├── train_model.py    # Fine-tune a model on (scenario text → Petri-net JSON)
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
    *   `--interactive-theme`: Prompt the user for a theme before generating samples.
    *Example:*
    ```bash
    python src/main.py forward_gen --interactive-theme --num_forward_samples 1 --num_few_shot 3
    ```
    During this process, candidates are saved in `outputs/review_temp/`. You will be prompted in the console to approve or reject each candidate.

3.  **`generate_from_text`** (alias: **`gft`**): Generate Petri-Net JSON from ad-hoc scenario text.
    *   Takes scenario text, generates Petri Net JSON, and saves the input text, output JSON, and a PDF visualization to a new numbered subfolder in `outputs/generated_from_text/`.
    *   `--scenario_text <text>` (aliases: `-s`, `--text`): Your scenario description. If omitted, you'll be prompted interactively.
    *   `--num_few_shot <N>` (alias: `-nfs`): Number of hand-made examples to use for few-shot prompting (default: 0).
    *   `--model_name <model>` (alias: `-m`): Model to use (default: as configured, e.g., `gemini-2.5-flash-preview-05-20`).
    *   `--temperature <T>` (alias: `-t`): Sampling temperature for LLM (0.0-1.0, default: 0.2).
    *Example:*
    ```bash
    python src/main.py generate_from_text --scenario_text "A user watches a video, can pause it, and then resume."
    ```
    *Interactive Example (prompts for text):*
    ```bash
    python src/main.py gft --num_few_shot 1
    ```

4.  **`validate_sample`**: Validate an existing Petri net JSON file.
    *   `--sample_id <id>`: (Required) Stem of the sample file.
        *   For hand-made: e.g., `sample_01`.
        *   For synthesized: e.g., `gen_approved_abcdef12`.
    *   `--data_type <type>`: (Required) Choices: `hand_made`, `synthesized`.
    *Example:*
    ```bash
    python src/main.py validate_sample --sample_id gen_approved_2898622b --data_type synthesized
    python src/main.py validate_sample --sample_id sample_01 --data_type hand_made
    ```

5.  **`visualize_sample`**: Generate a new PDF visualization for an existing sample.
    *   `--sample_id <id>`: (Required) Stem of the sample file (same as for `validate_sample`).
    *   `--data_type <type>`: (Required) Choices: `hand_made`, `synthesized`.
    *The visualization will be saved in `outputs/review_temp/`*
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

## Fine-tuning (Experimental – Non-functional)

> **Warning:** This fine-tuning workflow is experimental, does not function correctly, and produces invalid results. It is provided for illustration only and should **not** be used.

Dependencies (for reference):

```bash
pip install transformers datasets
```

Usage (reference only – results will be incorrect):

```bash
python src/train_model.py \
  --model <model_name> \
  --train_ratio 0.8 \
  --epochs 3
```

The script will:

*   Gather all `*_text.txt` + `*_petri.json` pairs from `outputs/synthesized_data/approved/`.
*   Shuffle and split into `outputs/train_data/` and `outputs/val_data/` (as JSON records).
*   Tokenize inputs and targets.
*   Launch a Trainer with a `compute_loss` hook ready for a semantic Petri-net loss.

## Acknowledgments
*   Google for the Gemini Pro API.
*   The creators of Graphviz and `jsonschema`.