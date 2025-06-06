# src/data_synthesis.py
import json
import uuid
from pathlib import Path
import shutil

from llm_interaction import get_llm_response
from validation import validate_petri_net_json, save_auto_rejected_sample
from petri_net_utils import petri_json_to_dot
from config import (
    SYNTHESIZED_APPROVED_DIR,
    SYNTHESIZED_REJECTED_MANUAL_DIR,
    HAND_MADE_DIR,
    REVIEW_TEMP_DIR,
)


# --- Helper function to load hand-made samples ---
def load_hand_made_sample(sample_id_str):
    text_path = HAND_MADE_DIR / f"{sample_id_str}_text.txt"
    json_path = HAND_MADE_DIR / f"{sample_id_str}_petri.json"
    if not text_path.exists():
        print(f"Error: Text file not found for sample {sample_id_str} at {text_path}")
        return None, None
    if not json_path.exists():
        print(f"Error: JSON file not found for sample {sample_id_str} at {json_path}")
        return None, None
    try:
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()
        with open(json_path, "r", encoding="utf-8") as f:
            petri_json = json.load(f)
        return text, petri_json
    except Exception as e:
        print(f"Error loading hand-made sample {sample_id_str}: {e}")
        return None, None


# --- Helper to get next available numbered folder for approved samples ---
def get_next_approved_folder_index(approved_dir: Path):
    approved_dir.mkdir(parents=True, exist_ok=True)
    max_index = 0
    for item in approved_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            try:
                max_index = max(max_index, int(item.name))
            except ValueError:
                continue
    return max_index + 1


# --- Helper to save final samples (text, JSON) to specific directories ---
def save_final_sample_files(
    text_content,
    petri_json_data,
    target_parent_dir: Path,
    original_candidate_base: str,
    status_suffix: str,
    use_numbered_subfolder: bool = True,
):
    """Saves text and JSON. Approved samples go into numbered subfolders."""
    if "candidate_" in original_candidate_base:
        name_parts = original_candidate_base.split("_")
        uuid_part = name_parts[-1] if len(name_parts) > 1 else original_candidate_base
        clean_base_name = "gen"
    else:
        uuid_part = original_candidate_base
        clean_base_name = "gen"

    final_filename_stem = f"{clean_base_name}_{status_suffix}_{uuid_part}"

    actual_save_dir = target_parent_dir
    if status_suffix == "approved" and use_numbered_subfolder:
        next_index = get_next_approved_folder_index(target_parent_dir)
        actual_save_dir = target_parent_dir / f"{next_index:04d}"

    actual_save_dir.mkdir(parents=True, exist_ok=True)

    text_output_path = actual_save_dir / f"{final_filename_stem}_text.txt"
    json_output_path = actual_save_dir / f"{final_filename_stem}_petri.json"

    try:
        with open(text_output_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(petri_json_data, f, indent=2)
        print(f"  Text/JSON permanently saved to: {actual_save_dir.resolve()}")
        print(f"    Files: {text_output_path.name}, {json_output_path.name}")
        return actual_save_dir, final_filename_stem
    except Exception as e:
        print(f"  Error saving final text/JSON to {actual_save_dir.resolve()}: {e}")
        return None, None


def synthesize_paraphrases(
    original_text,
    original_petri_json,
    num_paraphrases=3,
    sample_base_name="paraphrase_source",
):
    print(
        f"\nSynthesizing {num_paraphrases} paraphrases for text starting with: '{original_text[:70]}...'"
    )
    system_instruction = (
        "You are an expert in natural language processing. Your task is to paraphrase a given scenario "
        "description multiple times, ensuring each paraphrase retains the exact same underlying logic as the original."
    )
    user_prompt = f"""
Original Scenario Text:
---
{original_text}
---
Corresponding Petri Net JSON (for your understanding of the logic to preserve):
---
{json.dumps(original_petri_json, indent=2)}
---
Generate {num_paraphrases} diverse paraphrases of the Original Scenario Text.
Separate paraphrases with '---PARAPHRASE_SEPARATOR---'.
"""
    response_content_str = get_llm_response(
        prompt_text=user_prompt,
        system_instruction=system_instruction,
        temperature=0.7,
        json_mode=False,
    )
    if not response_content_str:
        print("Failed to get paraphrases from LLM.")
        return

    paraphrases_list = response_content_str.split("---PARAPHRASE_SEPARATOR---")
    generated_count = 0
    for i, paraphrase_text in enumerate(paraphrases_list):
        paraphrase_text = paraphrase_text.strip()
        if paraphrase_text:
            print(f"  Generated Paraphrase {i+1}: '{paraphrase_text[:100]}...'")
            paraphrase_candidate_base = f"{sample_base_name}_paraphrase{i+1}"
            save_final_sample_files(
                paraphrase_text,
                original_petri_json,
                SYNTHESIZED_APPROVED_DIR,
                paraphrase_candidate_base,  # Use this as the "original_candidate_base" for naming
                "approved",  # Paraphrases are auto-approved
                use_numbered_subfolder=True,
            )
            generated_count += 1
            if generated_count >= num_paraphrases:
                break
    if generated_count == 0:
        print("No valid paraphrases extracted.")
    else:
        print(
            f"Saved {generated_count} paraphrased samples to {SYNTHESIZED_APPROVED_DIR.resolve()}."
        )


# --- Helper to build few-shot prompt string ---
def build_few_shot_prompt_from_handmade(num_examples=2):
    prompt_str = ""
    loaded_count = 0
    if not isinstance(HAND_MADE_DIR, Path):
        print("Error: HAND_MADE_DIR is not a valid Path object in config.")
        return ""
    sample_files = sorted(list(HAND_MADE_DIR.glob("sample_*_text.txt")))
    for text_file_path in sample_files:
        sample_id_str = text_file_path.name.replace("_text.txt", "")
        text, petri_json = load_hand_made_sample(sample_id_str)
        if text and petri_json:
            prompt_str += f'Example {loaded_count + 1}:\nScenario Text:\n"""\n{text.strip()}\n"""\n\n'
            prompt_str += f"Corresponding Petri Net JSON:\n```json\n{json.dumps(petri_json, indent=2)}\n```\n---\n"
            loaded_count += 1
            if loaded_count >= num_examples:
                break
    if loaded_count == 0:
        print(
            f"Warning: No hand-made samples found in {HAND_MADE_DIR} for few-shot examples."
        )
    else:
        print(f"Built few-shot prompt using {loaded_count} example(s).")
    return prompt_str


def synthesize_forward_generation(
    few_shot_examples_text, num_new_samples=1, theme=None
):
    print(
        f"\nAttempting forward generation of {num_new_samples} new (Text, JSON) pair(s)..."
    )
    if theme:
        print(f"Using theme: '{theme}'")
    theme_instruction = f"Theme: {theme}\n\n" if theme else ""

    # --- FULL System Instruction (ensure your complete prompt is here) ---
    system_instruction = f"""
You are an expert in modeling multimedia scenarios using Petri Nets.
Your primary task is to generate NEW, creative, and plausible multimedia scenario descriptions AND their corresponding Petri Net data structures in JSON format.
The Petri Net JSON MUST strictly adhere to the following schema:
{{ "places": {{...}}, "transitions": {{...}}, "arcs": [{{...}}], "initial": {{...}} }}
Key constraints for the JSON:
1. Unique IDs for places/transitions.
2. Descriptive labels.
3. Valid arc references.
4. Arcs connect places-to-transitions or transitions-to-places only.
5. Valid initial marking place IDs.
6. Logical accuracy to scenario text.
7. Mix of sequences, choices, concurrency.
8. All nodes connected (unless trivial net).
9. Model "return to menu" or "play again" as cycles back to earlier places, not new terminal states.
10. Actions generally available for a primary state should be accessible from its sub-modes unless explicitly restricted.
You MUST output your response as a single, valid JSON object for EACH generated sample with "scenario_text" and "petri_net_json" keys.
Example (looping):
{{
  "scenario_text": "User interacts with a kiosk. From the main screen, they can select 'Info' or 'Order'. If 'Info', details are shown, then they return to main screen. If 'Order', they go through ordering steps and then return to main screen. The main screen is the initial state.",
  "petri_net_json": {{
    "places": {{"p_main": "Main Screen", "p_info_shown": "Info Shown", "p_ordering": "Ordering Process"}},
    "transitions": {{"t_select_info": "Select Info", "t_select_order": "Select Order", "t_finish_info": "Finish Info Viewing", "t_complete_order": "Complete Order"}},
    "arcs": [
      {{"from": "p_main", "to": "t_select_info"}}, {{"from": "t_select_info", "to": "p_info_shown"}},
      {{"from": "p_info_shown", "to": "t_finish_info"}}, {{"from": "t_finish_info", "to": "p_main"}},
      {{"from": "p_main", "to": "t_select_order"}}, {{"from": "t_select_order", "to": "p_ordering"}},
      {{"from": "p_ordering", "to": "t_complete_order"}}, {{"from": "t_complete_order", "to": "p_main"}}
    ],
    "initial": {{"p_main": 1}}
  }}
}}
"""
    # --- FULL User Prompt Template (ensure your complete template is here) ---
    user_prompt_template = f"""{theme_instruction}Here are some examples of existing (Scenario Text, Petri Net JSON) pairs to guide your generation style and complexity. Learn from these:
--- FEW-SHOT EXAMPLES START ---
{few_shot_examples_text}
--- FEW-SHOT EXAMPLES END ---

Now, based on these examples and your expertise as defined in the system instructions, please generate ONE new, distinct multimedia scenario (text) and its corresponding Petri Net JSON.
Ensure your output is a single JSON object adhering strictly to the format specified in the system instructions (containing 'scenario_text' and 'petri_net_json' keys).
"""
    generated_and_approved_count = 0

    for i in range(num_new_samples):
        print(
            f"\n--- Generating Forward Sample Candidate {i+1} of {num_new_samples} ---"
        )
        candidate_id_base = f"candidate_{uuid.uuid4().hex[:8]}"

        generated_pair_dict = get_llm_response(
            prompt_text=user_prompt_template,
            system_instruction=system_instruction,
            json_mode=True,
            temperature=1.0,
        )
        if not generated_pair_dict or not isinstance(generated_pair_dict, dict):
            save_auto_rejected_sample(
                generated_pair_dict or {}, "", "llm_response_error", candidate_id_base
            )
            continue
        new_text, new_petri_json = generated_pair_dict.get(
            "scenario_text"
        ), generated_pair_dict.get("petri_net_json")
        if not all(
            [
                new_text,
                isinstance(new_text, str),
                new_petri_json,
                isinstance(new_petri_json, dict),
            ]
        ):
            save_auto_rejected_sample(
                generated_pair_dict,
                new_text or "No text",
                "llm_malformed_output",
                candidate_id_base,
            )
            continue
        print(f"  Candidate Scenario Text: '{new_text[:100]}...'")

        is_structurally_valid, validation_msg = validate_petri_net_json(new_petri_json)
        if not is_structurally_valid:
            print(f"  AUTO-REJECTED (Structural): {validation_msg}")
            save_auto_rejected_sample(
                new_petri_json, new_text, validation_msg, candidate_id_base
            )
            continue
        print("  Automated Structural Validation PASSED.")

        REVIEW_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        temp_text_path = REVIEW_TEMP_DIR / f"{candidate_id_base}_text.txt"
        temp_json_path = REVIEW_TEMP_DIR / f"{candidate_id_base}_petri.json"

        temp_pdf_for_review: Path | None = None

        try:
            with open(temp_text_path, "w", encoding="utf-8") as f:
                f.write(new_text)
            with open(temp_json_path, "w", encoding="utf-8") as f:
                json.dump(new_petri_json, f, indent=2)
        except Exception as e:
            print(f"  Warning: Could not save candidate text/JSON to review_temp: {e}")
            continue

        print(
            f"  Candidate text/JSON for review in: {REVIEW_TEMP_DIR.resolve()} (ID: {candidate_id_base})"
        )

        try:
            pdf_path_obj, _ = petri_json_to_dot(
                new_petri_json, filename=candidate_id_base, output_dir=REVIEW_TEMP_DIR
            )
            if pdf_path_obj and pdf_path_obj.exists():
                temp_pdf_for_review = pdf_path_obj
                print(
                    f"  Visualization for review (PDF): {temp_pdf_for_review.resolve()}"
                )
            else:
                print(f"  PDF Visualization generation for review failed.")
        except Exception as e:
            print(f"  Warning: Error calling petri_json_to_dot for review: {e}")

        # --- Manual Review Prompt ---
        print("\n" + "=" * 50 + "\n  >>> MANUAL REVIEW REQUIRED <<< \n" + "=" * 50)
        print(
            f"  Reviewing Candidate ID: {candidate_id_base}\n  Files for review are in: {REVIEW_TEMP_DIR.resolve()}"
        )
        if temp_text_path.exists():
            print(f"    Text: {temp_text_path.name}")
        if temp_json_path.exists():
            print(f"    JSON: {temp_json_path.name}")
        if temp_pdf_for_review:
            print(f"    Viz PDF: {temp_pdf_for_review.name}")
        print(
            f"\n  Full Scenario Text:\n{new_text}\n\n  Full Petri Net JSON:\n{json.dumps(new_petri_json, indent=2)}\n"
        )

        user_approval = ""
        while user_approval not in ["yes", "no", "y", "n"]:
            user_approval = input("  Approve candidate? (yes/no/y/n): ").strip().lower()
        print("=" * 50 + "\n")

        is_approved = user_approval in ["yes", "y"]
        target_parent_dir_for_sample = (
            SYNTHESIZED_APPROVED_DIR if is_approved else SYNTHESIZED_REJECTED_MANUAL_DIR
        )
        status_suffix_for_sample = "approved" if is_approved else "rejected_manual"

        final_save_dir, final_filename_stem = save_final_sample_files(
            new_text,
            new_petri_json,
            target_parent_dir_for_sample,
            candidate_id_base,
            status_suffix_for_sample,
            use_numbered_subfolder=is_approved,
        )

        if final_save_dir and final_filename_stem:
            if is_approved:
                generated_and_approved_count += 1
            print(
                f"  Sample {status_suffix_for_sample}. Text/JSON saved to: {final_save_dir.resolve()}"
            )

            print(
                f"  Generating final PDF visualization in: {final_save_dir.resolve()}"
            )
            final_pdf_path, _ = petri_json_to_dot(
                new_petri_json,
                filename=final_filename_stem,
                output_dir=final_save_dir,
            )
            if final_pdf_path and final_pdf_path.exists():
                print(f"  Final PDF visualization saved: {final_pdf_path.resolve()}")
            else:
                print(f"  Failed to generate final PDF visualization")
        else:
            print("  Error during final saving of text/JSON.")

        # --- Cleanup temporary files from REVIEW_TEMP_DIR ---
        files_to_clean_in_review_temp = [temp_text_path, temp_json_path]
        if temp_pdf_for_review:
            files_to_clean_in_review_temp.append(temp_pdf_for_review)

        for f_path in files_to_clean_in_review_temp:
            if f_path and f_path.exists() and f_path.parent == REVIEW_TEMP_DIR:
                try:
                    f_path.unlink()
                except OSError as e:
                    print(
                        f"  Warning: Could not delete temp review file {f_path.name}: {e}"
                    )

    print(f"\nFinished. Approved and saved {generated_and_approved_count} samples.")
