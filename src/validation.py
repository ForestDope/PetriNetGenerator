import json
import uuid
from jsonschema import validate, ValidationError
from src.config import (
    PETRI_NET_SCHEMA_PATH,
    OUTPUTS_DIR,
    INVALID_AUTO_REJECTED_DIR,
)
from pathlib import Path


def load_petri_net_schema():
    """Loads the Petri Net JSON schema from the predefined path."""
    if not PETRI_NET_SCHEMA_PATH.exists():
        print(f"CRITICAL: Petri Net schema file not found at {PETRI_NET_SCHEMA_PATH}")
        return None
    try:
        with open(PETRI_NET_SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        print("Petri Net JSON schema loaded successfully.")
        return schema
    except Exception as e:
        print(f"Error loading Petri Net JSON schema: {e}")
        return None


PETRI_NET_SCHEMA = load_petri_net_schema()


def validate_petri_net_json(petri_json_data):
    """
    Validates Petri Net JSON data against the loaded schema and performs
    additional logical checks (e.g., arc consistency, isolated nodes).

    Args:
        petri_json_data (dict): The Petri Net data in dictionary format.

    Returns:
        tuple: (bool, str) where bool is True if valid, False otherwise,
               and str is a message ("Valid" or error details).
    """
    if PETRI_NET_SCHEMA is None:
        return False, "Schema not loaded. Cannot validate."
    if not isinstance(petri_json_data, dict):
        return False, "Invalid input: petri_json_data must be a dictionary."

    try:
        # 1. Basic schema validation using jsonschema
        validate(instance=petri_json_data, schema=PETRI_NET_SCHEMA)

        # 2. More sophisticated logical checks
        places = petri_json_data.get("places", {})
        transitions = petri_json_data.get("transitions", {})
        arcs = petri_json_data.get("arcs", [])
        initial_marking_places = set(petri_json_data.get("initial", {}).keys())

        all_defined_node_ids = set(places.keys()) | set(transitions.keys())
        nodes_in_arcs = set()  # To store all node IDs that appear in any arc

        # Check arc consistency and gather nodes involved in arcs
        for i, arc in enumerate(arcs):
            arc_from = arc.get("from")
            arc_to = arc.get("to")

            if not arc_from or not arc_to:  # Check for missing from/to keys
                return False, f"Arc {i} is malformed: missing 'from' or 'to' field."

            if arc_from not in all_defined_node_ids:
                return (
                    False,
                    f"Arc {i} 'from' node '{arc_from}' not found in defined places or transitions.",
                )
            if arc_to not in all_defined_node_ids:
                return (
                    False,
                    f"Arc {i} 'to' node '{arc_to}' not found in defined places or transitions.",
                )

            nodes_in_arcs.add(arc_from)
            nodes_in_arcs.add(arc_to)

            # Prevent self-loops to the same type of node
            if (arc_from in places and arc_to in places) or (
                arc_from in transitions and arc_to in transitions
            ):
                return (
                    False,
                    f"Arc {i} from '{arc_from}' to '{arc_to}' is invalid: Cannot connect same node types directly (e.g., place-to-place or transition-to-transition).",
                )

        # Check initial marking consistency
        for place_id in initial_marking_places:
            if place_id not in places:
                return (
                    False,
                    f"Initial marking for place '{place_id}' is invalid: Place ID not defined in 'places'.",
                )

        if arcs:
            for p_id in places:
                if p_id not in nodes_in_arcs and p_id not in initial_marking_places:
                    if len(all_defined_node_ids) > 1:
                        return (
                            False,
                            f"Validation Error: Place '{p_id}' ('{places[p_id]}') is isolated (not part of any arc and not an initial marking).",
                        )
            for t_id in transitions:
                if t_id not in nodes_in_arcs:
                    if len(all_defined_node_ids) > 1:
                        return (
                            False,
                            f"Validation Error: Transition '{t_id}' ('{transitions[t_id]}') is isolated (not part of any arc).",
                        )
        elif not arcs and (
            len(places) > 1
            or len(transitions) > 1
            or (len(places) == 1 and len(transitions) == 1)
        ):
            return (
                False,
                "Validation Error: Multiple places/transitions exist but no arcs are defined to connect them.",
            )
        elif not arcs and (len(places) + len(transitions) > 1):
            return (
                False,
                "Validation Error: Multiple nodes exist but no arcs connect them.",
            )

        return True, "Valid"
    except ValidationError as e:
        error_path = " -> ".join(map(str, e.path)) if e.path else "root"
        return False, f"JSON Schema Validation Error at '{error_path}': {e.message}"
    except Exception as e:
        return False, f"An unexpected error occurred during validation: {str(e)}"


# --- Helper to save invalid JSONs (auto-rejected) ---
def save_auto_rejected_sample(
    petri_json_data, scenario_text, reason, original_filename_base="unknown_candidate"
):
    """Saves the auto-rejected (structurally invalid) Petri Net JSON to a dedicated directory."""
    try:
        timestamp = uuid.uuid4().hex[:8]
        safe_reason = "".join(c if c.isalnum() else "_" for c in reason[:30])

        invalid_filename_base = (
            f"{original_filename_base}_autorejected_{safe_reason}_{timestamp}"
        )

        output_json_path = (
            INVALID_AUTO_REJECTED_DIR / f"{invalid_filename_base}_petri.json"
        )
        output_text_path = (
            INVALID_AUTO_REJECTED_DIR / f"{invalid_filename_base}_text.txt"
        )

        with open(output_json_path, "w", encoding="utf-8") as f_json:
            json.dump(petri_json_data, f_json, indent=2)

        if scenario_text:
            with open(output_text_path, "w", encoding="utf-8") as f_text:
                f_text.write(scenario_text)

        print(
            f"  --> Auto-rejected sample saved for review to: {INVALID_AUTO_REJECTED_DIR.resolve()}"
        )
        print(f"      Files: {output_json_path.name}, {output_text_path.name}")
    except Exception as e:
        print(f"  Warning: Could not save auto-rejected invalid sample: {e}")
