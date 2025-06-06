# src/adhoc_generation.py
import json

# Assuming these are in src/ or your PYTHONPATH is set correctly
from llm_interaction import get_llm_response
from data_synthesis import (
    build_few_shot_prompt_from_handmade,
)  # To get few-shot examples

# config.LLM_MODEL_GEMINI will be passed from main.py


def generate_petri_net_from_text(
    scenario_text_input: str,
    num_few_shot: int,
    model_name: str,  # Passed from main.py
    temperature: float,  # Passed from main.py
    system_instruction_override: str | None = None,  # Optional override
) -> dict | None:
    """
    Core logic to generate Petri Net JSON from provided text.
    Takes all necessary parameters including model_name and temperature.
    Returns the generated JSON data as a dictionary, or None on failure.
    """
    few_shot_prompt_part = ""
    if num_few_shot > 0:
        few_shot_prompt_part = build_few_shot_prompt_from_handmade(num_few_shot)
        if not few_shot_prompt_part:
            print(
                f"Warning: Could not build {num_few_shot} few-shot examples. Proceeding without them or check hand_made data."
            )
        else:
            few_shot_prompt_part += "\n--- FEW-SHOT EXAMPLES END ---\n\n"

    # System instructions
    # Use override if provided, otherwise use the default
    system_instruction_to_use = (
        system_instruction_override
        if system_instruction_override
        else """
You are an expert in modeling multimedia scenarios using Petri Nets.
Your task is to take the user-provided scenario description and output exactly one JSON object with keys
  - "scenario_text": echoing the input text
  - "petri_net_json": a valid Petri Net in JSON form
The Petri Net MUST adhere to this schema:
{ "places": {...}, "transitions": {...}, "arcs": [...], "initial": {...} }
And to these constraints:
1. Unique IDs for places/transitions.
2. Descriptive labels.
3. Valid arc references.
4. Only place→transition or transition→place arcs.
5. Valid initial markings.
6. Logical fidelity to the scenario text.
7. Mix of sequences, choices, concurrency.
8. All nodes connected (unless trivial).
9. Model cycles as returns, not new terminal states.
10. Actions available in a state must be accessible in its sub-modes.
Output just the JSON—no extra commentary.
"""
    )

    user_prompt = f'{few_shot_prompt_part}Now, process the following scenario text:\n\nScenario Text:\n"""\n{scenario_text_input}\n"""'

    # print(f"\n[DEBUG Adhoc Gen] Sending prompt to LLM (Model: {model_name}, Temp: {temperature})...")
    # print(f"[DEBUG Adhoc Gen] System Instruction: {system_instruction_to_use[:100]}...")
    # print(f"[DEBUG Adhoc Gen] User Prompt: {user_prompt[:200]}...")

    response_data = get_llm_response(
        prompt_text=user_prompt,
        system_instruction=system_instruction_to_use,
        model_name=model_name,
        temperature=temperature,
        json_mode=True,
    )

    if not response_data:
        # get_llm_response should print its own errors
        return None

    return response_data
