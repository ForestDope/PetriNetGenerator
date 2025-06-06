# src/adhoc_generation.py
import json

from llm_interaction import get_llm_response
from data_synthesis import build_few_shot_prompt_from_handmade


def generate_petri_net_from_text(
    scenario_text_input: str,
    num_few_shot: int,
    model_name: str,
    temperature: float,
    system_instruction_override: str | None = None,
) -> dict | None:
    """Core logic to generate Petri Net JSON from provided text."""
    few_shot_prompt_part = ""
    if num_few_shot > 0:
        few_shot_prompt_part = build_few_shot_prompt_from_handmade(num_few_shot)
        if not few_shot_prompt_part:
            print(f"Warning: Could not build {num_few_shot} few-shot examples.")
        else:
            few_shot_prompt_part += "\n--- FEW-SHOT EXAMPLES END ---\n\n"

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

    response_data = get_llm_response(
        prompt_text=user_prompt,
        system_instruction=system_instruction_to_use,
        model_name=model_name,
        temperature=temperature,
        json_mode=True,
    )

    if not response_data:
        return None

    return response_data
