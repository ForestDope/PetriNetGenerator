# src/main.py
import argparse
import json
import sys
from pathlib import Path
import uuid

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data_synthesis import (
    synthesize_paraphrases,
    synthesize_forward_generation,
    load_hand_made_sample,
    build_few_shot_prompt_from_handmade,
    get_next_approved_folder_index,
)
from src.validation import validate_petri_net_json
from src.petri_net_utils import petri_json_to_dot
from src.config import (
    HAND_MADE_DIR,
    SYNTHESIZED_APPROVED_DIR,
    SYNTHESIZED_REJECTED_MANUAL_DIR,
    REVIEW_TEMP_DIR,
    GOOGLE_API_KEY,
    LLM_MODEL_GEMINI,
    GENERATED_FROM_TEXT_DIR,
)

from generate_from_text import generate_petri_net_from_text


def find_synthesized_file_in_dir(
    directory: Path, sample_id_stem: str, file_suffix: str
) -> Path | None:
    """Helper to find a file with a given stem and suffix in a directory."""
    target_file = directory / f"{sample_id_stem}{file_suffix}"
    if target_file.exists():
        return target_file
    return None


def find_synthesized_json_or_text(
    sample_id_stem: str, file_type: str = "_petri.json"
) -> Path | None:
    """Searches for a synthesized file based on its stem."""
    if SYNTHESIZED_APPROVED_DIR.exists():
        for numbered_folder in SYNTHESIZED_APPROVED_DIR.iterdir():
            if numbered_folder.is_dir() and numbered_folder.name.isdigit():
                found_file = find_synthesized_file_in_dir(
                    numbered_folder, sample_id_stem, file_suffix=file_type
                )
                if found_file:
                    return found_file

    if SYNTHESIZED_REJECTED_MANUAL_DIR.exists():
        found_file = find_synthesized_file_in_dir(
            SYNTHESIZED_REJECTED_MANUAL_DIR, sample_id_stem, file_suffix=file_type
        )
        if found_file:
            return found_file
    return None


def cli_paraphrase(args):
    if not args.sample_id:
        print("Error: --sample_id for paraphrasing.")
        return
    original_text, original_petri_json = load_hand_made_sample(args.sample_id)
    if original_text and original_petri_json:
        synthesize_paraphrases(
            original_text, original_petri_json, args.num_paraphrases, args.sample_id
        )
    else:
        print(f"Could not load hand-made sample '{args.sample_id}'.")


def get_user_theme():
    """Prompt user for a theme and return it."""
    print("\n" + "=" * 40)
    print("INTERACTIVE THEME MODE")
    print("=" * 40)
    while True:
        theme = input("Enter desired theme (e.g. 'nature', 'technology'): ").strip()
        if not theme:
            print("  Please enter a non-empty theme.\n")
            continue
        confirm = input(f"Confirm theme '{theme}'? (y/n): ").strip().lower()
        if confirm in ("y", "yes"):
            return theme
        print("Let's try again...\n")


def cli_forward_gen(args):
    theme = None
    if getattr(args, "interactive_theme", False):
        theme = get_user_theme()
    few_shot_prompt_text = build_few_shot_prompt_from_handmade(args.num_few_shot)
    if not few_shot_prompt_text:
        print("Error: Could not build few-shot examples.")
        return
    synthesize_forward_generation(few_shot_prompt_text, args.num_forward_samples, theme)


def cli_validate_sample(args):
    if not args.sample_id:
        print("Error: --sample_id for validation.")
        return

    json_file_to_load = None
    if args.data_type == "hand_made":
        json_file_to_load = HAND_MADE_DIR / f"{args.sample_id}_petri.json"
    elif args.data_type == "synthesized":
        json_file_to_load = find_synthesized_json_or_text(args.sample_id, "_petri.json")

    if json_file_to_load and json_file_to_load.exists():
        try:
            with open(json_file_to_load, "r", encoding="utf-8") as f:
                petri_data = json.load(f)
            is_valid, msg = validate_petri_net_json(petri_data)
            status = "VALID" if is_valid else f"INVALID: {msg}"
            print(f"Sample '{args.sample_id}' ({json_file_to_load.name}) is {status}.")
        except Exception as e:
            print(f"Error validating {json_file_to_load.name}: {e}")
    else:
        print(
            f"JSON file for sample ID '{args.sample_id}' (type: {args.data_type}) not found."
        )


def cli_visualize_sample(args):
    if not args.sample_id:
        print("Error: --sample_id for visualization.")
        return

    json_file_to_load = None
    viz_output_dir = REVIEW_TEMP_DIR
    viz_filename_stem = f"{args.data_type}_{args.sample_id}_adhoc_viz"

    if args.data_type == "hand_made":
        json_file_to_load = HAND_MADE_DIR / f"{args.sample_id}_petri.json"
    elif args.data_type == "synthesized":
        json_file_to_load = find_synthesized_json_or_text(args.sample_id, "_petri.json")

    if json_file_to_load and json_file_to_load.exists():
        try:
            with open(json_file_to_load, "r", encoding="utf-8") as f:
                petri_data = json.load(f)
            print(
                f"Generating visualization for '{args.sample_id}' in '{viz_output_dir.resolve()}'"
            )
            pdf_path, _ = petri_json_to_dot(
                petri_data, filename=viz_filename_stem, output_dir=viz_output_dir
            )
            if pdf_path:
                print(f"  Visualization generated: {pdf_path.resolve()}")
            else:
                print("  Visualization generation failed.")
        except Exception as e:
            print(f"Error visualizing {json_file_to_load.name}: {e}")
    else:
        print(
            f"JSON file for sample ID '{args.sample_id}' (type: {args.data_type}) not found."
        )


def cli_generate_from_text_handler(args):
    """CLI handler that calls the core logic and saves the output."""
    scenario_text_input = args.scenario_text
    if not scenario_text_input:
        try:
            print("No scenario text provided via --scenario_text argument.")
            scenario_text_input = input(
                "Enter scenario text (or Ctrl+D/Ctrl+Z+Enter for empty, Ctrl+C to cancel):\n> "
            ).strip()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return
        except EOFError:
            print("\nEmpty input received. Exiting.")
            return

    if not scenario_text_input:
        print("Error: Scenario text cannot be empty.")
        return

    print("\nGenerating Petri Net from your text...")
    generated_data = generate_petri_net_from_text(
        scenario_text_input=scenario_text_input,
        num_few_shot=args.num_few_shot,
        model_name=args.model_name,
        temperature=args.temperature,
    )

    if not generated_data:
        print("Failed to generate Petri Net data.")
        return

    llm_echoed_text = generated_data.get("scenario_text", scenario_text_input)
    petri_net_json = generated_data.get("petri_net_json")

    if not petri_net_json or not isinstance(petri_net_json, dict):
        print("Error: LLM output did not contain a valid 'petri_net_json' object.")
        print("LLM Raw Output:")
        print(json.dumps(generated_data, indent=2))
        return

    print("\n--- LLM Generated Output ---")
    print(json.dumps(generated_data, indent=2))

    next_index = get_next_approved_folder_index(GENERATED_FROM_TEXT_DIR)
    save_dir = GENERATED_FROM_TEXT_DIR / f"{next_index:04d}"
    save_dir.mkdir(parents=True, exist_ok=True)

    s_text_snippet = "".join(
        c if c.isalnum() else "_" for c in scenario_text_input[:20]
    ).strip("_")
    if not s_text_snippet:
        s_text_snippet = "adhoc"
    filename_stem = f"{s_text_snippet}_{uuid.uuid4().hex[:8]}"

    text_file_path = save_dir / f"{filename_stem}_scenario.txt"
    json_file_path = save_dir / f"{filename_stem}_petri.json"

    try:
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(llm_echoed_text)
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(petri_net_json, f, indent=2)
        print(f"\nOutput saved to directory: {save_dir.resolve()}")
        print(f"  Text: {text_file_path.name}")
        print(f"  JSON: {json_file_path.name}")

        # Generate and save visualization in the same directory
        print(f"  Generating visualization in: {save_dir.resolve()}")
        pdf_path, gv_path = petri_json_to_dot(
            petri_net_json,
            filename=filename_stem,
            output_dir=save_dir,
        )
        if pdf_path:
            print(f"  Visualization PDF: {pdf_path.name}")
        if not pdf_path and not gv_path:
            print(f"  Failed to generate visualization.")

    except Exception as e:
        print(f"\nError saving output files or generating visualization: {e}")


def main():
    if not GOOGLE_API_KEY and any(
        action in sys.argv for action in ["paraphrase", "forward_gen"]
    ):
        print("CRITICAL: GOOGLE_API_KEY is not set. LLM actions will fail.")

    parser = argparse.ArgumentParser(
        description="Petri Net Data Synthesis and Validation CLI.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="action", title="actions", required=True, help="Available actions."
    )

    p_paraphrase = subparsers.add_parser(
        "paraphrase", help="Generate paraphrases for a hand-made sample."
    )
    p_paraphrase.add_argument(
        "--sample_id",
        type=str,
        required=True,
        help="ID of hand-made sample (e.g., 'sample_01').",
    )
    p_paraphrase.add_argument(
        "--num_paraphrases",
        type=int,
        default=3,
        help="Number of paraphrases (default: 3).",
    )
    p_paraphrase.set_defaults(func=cli_paraphrase)

    p_forward_gen = subparsers.add_parser(
        "forward_gen", help="Generate new (Text, JSON) pairs via LLM."
    )
    p_forward_gen.add_argument(
        "--num_forward_samples",
        type=int,
        default=1,
        help="Number of new pairs (default: 1).",
    )
    p_forward_gen.add_argument(
        "--num_few_shot", type=int, default=2, help="Few-shot examples (default: 2)."
    )
    p_forward_gen.add_argument(
        "--interactive-theme",
        action="store_true",
        help="Ask user for a theme before generating samples",
    )
    p_forward_gen.set_defaults(func=cli_forward_gen)

    p_validate = subparsers.add_parser(
        "validate_sample", help="Validate a Petri Net JSON sample."
    )
    p_validate.add_argument(
        "--sample_id",
        type=str,
        required=True,
        help="Stem of the sample file.",
    )
    p_validate.add_argument(
        "--data_type",
        choices=["hand_made", "synthesized"],
        required=True,
        help="Type of data.",
    )
    p_validate.set_defaults(func=cli_validate_sample)

    p_visualize = subparsers.add_parser(
        "visualize_sample", help="Generate visualization for a sample."
    )
    p_visualize.add_argument(
        "--sample_id",
        type=str,
        required=True,
        help="Stem of the sample file.",
    )
    p_visualize.add_argument(
        "--data_type",
        choices=["hand_made", "synthesized"],
        required=True,
        help="Type of data.",
    )
    p_visualize.set_defaults(func=cli_visualize_sample)

    p_gft = subparsers.add_parser(
        "generate_from_text",
        aliases=["gft"],
        help="Generate Petri-Net JSON from scenario text.",
    )
    p_gft.add_argument(
        "--scenario_text",
        "-s",
        "--text",
        type=str,
        help="Your scenario description.",
    )
    p_gft.add_argument(
        "--num_few_shot",
        "-nfs",
        type=int,
        default=0,
        help="Number of few-shot examples (default: 0).",
    )
    p_gft.add_argument(
        "--model_name",
        "-m",
        type=str,
        default=LLM_MODEL_GEMINI,
        help=f"Model to use (default: {LLM_MODEL_GEMINI}).",
    )
    p_gft.add_argument(
        "--temperature",
        "-t",
        type=float,
        default=0.2,
        help="Sampling temperature for LLM (default: 0.2).",
    )
    p_gft.set_defaults(func=cli_generate_from_text_handler)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
