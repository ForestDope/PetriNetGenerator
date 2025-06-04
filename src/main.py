# src/main.py
import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data_synthesis import (
    synthesize_paraphrases,
    synthesize_forward_generation,
    load_hand_made_sample,
    build_few_shot_prompt_from_handmade
)
from src.validation import validate_petri_net_json
from src.petri_net_utils import petri_json_to_dot
from src.config import (
    HAND_MADE_DIR,
    SYNTHESIZED_APPROVED_DIR,
    SYNTHESIZED_REJECTED_MANUAL_DIR,
    # SYNTHESIZED_PARENT_DIR, # Not directly used by find, specific dirs are better
    REVIEW_TEMP_DIR, # For CLI to potentially inspect temp files if needed (though not primary use)
    GOOGLE_API_KEY
)

def find_synthesized_file_in_dir(directory: Path, sample_id_stem: str, file_suffix: str) -> Path | None:
    """Helper to find a file with a given stem and suffix in a directory."""
    # Tries exact match first: e.g., 0001_approved_abcdef12_petri.json
    # Then tries if sample_id_stem is just the unique part: e.g. 0001_approved_abcdef12
    # This depends on how user provides sample_id. Let's assume user provides the full stem.
    target_file = directory / f"{sample_id_stem}{file_suffix}" # e.g. xxxx_approved_yyyy_petri.json
    if target_file.exists():
        return target_file
    return None

def find_synthesized_json_or_text(sample_id_stem: str, file_type: str = "_petri.json") -> Path | None:
    """
    Searches for a synthesized file based on its stem (e.g., "gen_approved_abcdef12")
    in approved (numbered folders) and rejected_manual.
    file_type should be "_petri.json" or "_text.txt".
    """
    # Search in approved (inside numbered folders)
    if SYNTHESIZED_APPROVED_DIR.exists():
        for numbered_folder in SYNTHESIZED_APPROVED_DIR.iterdir():
            if numbered_folder.is_dir() and numbered_folder.name.isdigit():
                found_file = find_synthesized_file_in_dir(numbered_folder, sample_id_stem, file_suffix=file_type)
                if found_file:
                    return found_file

    # Search in rejected_manual (flat structure)
    if SYNTHESIZED_REJECTED_MANUAL_DIR.exists():
        found_file = find_synthesized_file_in_dir(SYNTHESIZED_REJECTED_MANUAL_DIR, sample_id_stem, file_suffix=file_type)
        if found_file:
            return found_file
    return None


def cli_paraphrase(args):
    if not args.sample_id: print("Error: --sample_id for paraphrasing."); return
    original_text, original_petri_json = load_hand_made_sample(args.sample_id)
    if original_text and original_petri_json:
        synthesize_paraphrases(original_text, original_petri_json, args.num_paraphrases, args.sample_id)
    else: print(f"Could not load hand-made sample '{args.sample_id}'.")

def cli_forward_gen(args):
    few_shot_prompt_text = build_few_shot_prompt_from_handmade(args.num_few_shot)
    if not few_shot_prompt_text: print("Error: Could not build few-shot examples."); return
    synthesize_forward_generation(few_shot_prompt_text, args.num_forward_samples)

def cli_validate_sample(args):
    if not args.sample_id: print("Error: --sample_id for validation."); return
    
    json_file_to_load = None
    if args.data_type == "hand_made":
        json_file_to_load = HAND_MADE_DIR / f"{args.sample_id}_petri.json"
    elif args.data_type == "synthesized":
        # User should provide the final filename stem, e.g., "gen_approved_abcdef12"
        json_file_to_load = find_synthesized_json_or_text(args.sample_id, "_petri.json")
    
    if json_file_to_load and json_file_to_load.exists():
        try:
            with open(json_file_to_load, 'r', encoding='utf-8') as f: petri_data = json.load(f)
            is_valid, msg = validate_petri_net_json(petri_data)
            status = "VALID" if is_valid else f"INVALID: {msg}"
            print(f"Sample '{args.sample_id}' ({json_file_to_load.name}) from '{json_file_to_load.parent}' is {status}.")
        except Exception as e: print(f"Error validating {json_file_to_load.name}: {e}")
    else:
        print(f"JSON file for sample ID stem '{args.sample_id}' (type: {args.data_type}) not found.")
        if args.data_type == "synthesized":
            print(f"  Searched in {SYNTHESIZED_APPROVED_DIR} (numbered subfolders) and {SYNTHESIZED_REJECTED_MANUAL_DIR}.")
            print(f"  Expected sample_id to be the file stem like 'gen_approved_abcdef12'.")


def cli_visualize_sample(args):
    if not args.sample_id: print("Error: --sample_id for visualization."); return

    json_file_to_load = None
    # For visualizing an existing sample, we find its JSON, then generate a NEW viz in REVIEW_TEMP_DIR
    # because the original viz should already be co-located if it's a synthesized sample.
    # If it's hand_made, we generate one in REVIEW_TEMP_DIR too for consistency of this command's output.
    
    viz_output_dir = REVIEW_TEMP_DIR # All ad-hoc visualizations go here for CLI
    viz_filename_stem = f"{args.data_type}_{args.sample_id}_adhoc_viz" # Unique name for this ad-hoc viz

    if args.data_type == "hand_made":
        json_file_to_load = HAND_MADE_DIR / f"{args.sample_id}_petri.json"
    elif args.data_type == "synthesized":
        json_file_to_load = find_synthesized_json_or_text(args.sample_id, "_petri.json")
    
    if json_file_to_load and json_file_to_load.exists():
        try:
            with open(json_file_to_load, 'r', encoding='utf-8') as f: petri_data = json.load(f)
            print(f"Generating ad-hoc visualization for '{args.sample_id}' in '{viz_output_dir.resolve()}'")
            pdf_path, _ = petri_json_to_dot(petri_data, filename=viz_filename_stem, output_dir=viz_output_dir)
            if pdf_path: print(f"  New visualization generated: {pdf_path.resolve()}")
            else: print("  Visualization generation failed.")
        except Exception as e: print(f"Error visualizing {json_file_to_load.name}: {e}")
    else:
        print(f"JSON file for sample ID stem '{args.sample_id}' (type: {args.data_type}) not found for visualization.")


def main():
    if not GOOGLE_API_KEY and any(action in sys.argv for action in ["paraphrase", "forward_gen"]):
        print("CRITICAL: GOOGLE_API_KEY is not set. LLM actions will fail.")

    parser = argparse.ArgumentParser(
        description="Petri Net Data Synthesis and Validation CLI.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="action", title="actions", required=True, help="Available actions.")

    p_paraphrase = subparsers.add_parser("paraphrase", help="Generate paraphrases for a hand-made sample.")
    p_paraphrase.add_argument("--sample_id", type=str, required=True, help="ID of hand-made sample (e.g., 'sample_01').")
    p_paraphrase.add_argument("--num_paraphrases", type=int, default=3, help="Number of paraphrases (default: 3).")
    p_paraphrase.set_defaults(func=cli_paraphrase)

    p_forward_gen = subparsers.add_parser("forward_gen", help="Generate new (Text, JSON) pairs via LLM.")
    p_forward_gen.add_argument("--num_forward_samples", type=int, default=1, help="Number of new pairs (default: 1).")
    p_forward_gen.add_argument("--num_few_shot", type=int, default=2, help="Few-shot examples (default: 2).")
    p_forward_gen.set_defaults(func=cli_forward_gen)

    p_validate = subparsers.add_parser("validate_sample", help="Validate a Petri Net JSON sample.")
    p_validate.add_argument("--sample_id", type=str, required=True,
                              help="Stem of the sample file. For hand_made: 'sample_01'. For synthesized: e.g., 'gen_approved_abcdef12'.")
    p_validate.add_argument("--data_type", choices=["hand_made", "synthesized"], required=True, help="Type of data.")
    p_validate.set_defaults(func=cli_validate_sample)

    p_visualize = subparsers.add_parser("visualize_sample", help="Generate new visualization for a sample.")
    p_visualize.add_argument("--sample_id", type=str, required=True, help="Stem of the sample file (same as for validate).")
    p_visualize.add_argument("--data_type", choices=["hand_made", "synthesized"], required=True, help="Type of data.")
    p_visualize.set_defaults(func=cli_visualize_sample)

    args = parser.parse_args()
    if hasattr(args, 'func'): args.func(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()