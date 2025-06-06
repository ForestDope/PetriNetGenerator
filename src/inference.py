import argparse
import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def main(
    model_dir: str,
    max_length: int,
    num_beams: int,
    temperature: float,
    top_p: float,
    repetition_penalty: float,
    length_penalty: float,
    device: str,
):
    # If top‐level dir has no config.json, pick latest "checkpoint-*" subfolder
    cfg = Path(model_dir) / "config.json"
    if not cfg.exists():
        ckpts = [
            d
            for d in Path(model_dir).iterdir()
            if d.is_dir() and d.name.startswith("checkpoint")
        ]
        if not ckpts:
            raise ValueError(
                f"No config.json in {model_dir} and no checkpoint-* subdirs found."
            )
        # sort by numeric suffix
        ckpts_sorted = sorted(ckpts, key=lambda d: int(d.name.split("-")[-1]))
        model_dir = str(ckpts_sorted[-1])

    # 1) load tokenizer & model
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir).to(device)

    # 2) get user input
    scenario = input("Enter multimedia scenario description:\n").strip()
    if not scenario:
        print("No input provided, exiting.")
        return

    # 3) build prompt
    prefix = (
        "Below is a multimedia scenario. Generate **only** the Petri-net JSON.\n\n"
        "Scenario:\n"
    )
    prompt = f"{prefix}{scenario}\n\nJSON:"
    print("\n[DEBUG] Model prompt:\n" + prompt + "\n")

    # 4) tokenize
    inputs = tokenizer(
        prompt, return_tensors="pt", truncation=True, padding=True, max_length=512
    ).to(device)

    # 5) generate with tuned params
    outputs = model.generate(
        **inputs,
        max_length=max_length,
        num_beams=num_beams,
        temperature=temperature,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        length_penalty=length_penalty,
        early_stopping=True,
        no_repeat_ngram_size=3,
    )

    # 6) decode & extract JSON
    gen = tokenizer.decode(outputs[0], skip_special_tokens=True)
    start, end = gen.find("{"), gen.rfind("}")
    json_str = gen[start : end + 1] if start >= 0 and end > start else gen
    try:
        petri = json.loads(json_str)
        print("\nGenerated Petri-net JSON:\n", json.dumps(petri, indent=2))
    except json.JSONDecodeError:
        print("\nFailed to parse JSON. Raw output:\n", gen)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="JSON‐only inference")
    p.add_argument("--model_dir", default="outputs/model_checkpoints")
    p.add_argument("--max_length", type=int, default=512)
    p.add_argument("--num_beams", type=int, default=4)
    p.add_argument("--temperature", type=float, default=0.0, help="0.0 = greedy")
    p.add_argument("--top_p", type=float, default=0.9)
    p.add_argument("--repetition_penalty", type=float, default=2.0)
    p.add_argument("--length_penalty", type=float, default=1.0)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()
    main(**vars(args))
