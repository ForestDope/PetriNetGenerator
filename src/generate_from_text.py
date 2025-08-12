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
{ "places": {...}, "transitions": {...}, "arcs": [...], "initial": {} }
And to these constraints, with a **focus on distinguishing between primary tasks (places) and key trigger events (transitions)**:

1.  Unique IDs for places/transitions.
2.  Descriptive labels.
3.  Valid arc references.
4.  Only place→transition or transition→place arcs.
5.  Valid initial markings.
6.  Logical fidelity to the scenario text.
7.  Mix of sequences, choices, concurrency.
8.  All nodes connected (unless trivial).
9.  Model cycles as returns to initial or well-defined stable states, not new terminal states.
10. Actions available in a state must be accessible in its sub-modes.

**Required Abstraction Level: High-Level and Direct**
The model must be a high-level, direct representation of the scenario's core logic. It must focus on the main sequence of tasks and the key events that trigger them.
- **AVOID SUPERFLUOUS DETAIL:** A single system action (like "opening a door") must not be broken down into multiple places and transitions (e.g., a place for 'door is opening', a transition for 'door open completed', and another place for 'door is open'). This level of detail is incorrect for this task.

**General Guidance for Petri Net Element Interpretation:**

* **Places (circles):** Represent a **distinct, primary system task or a significant, stable state**. A single place should represent the entire primary task at hand.
    * For example: `Ouvrir Porte Intérieure` is a valid place representing the system's current main task. A place for `Porte Intérieure S'Ouvre` would be incorrectly detailed.

* **Transitions (rectangles):** Represent the **single, significant, and instantaneous event** that causes the system to move from one primary task to the next.
    * **Valid examples:** `Personne Détectée`, `Demande d'Entrée`, `Durée Prédéfinie Écoulée`.
    * A transition should represent the *trigger* for the next main task, not the completion of a sub-step of a previous one.

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
