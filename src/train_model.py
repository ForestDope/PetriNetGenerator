import json, random, argparse
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Trainer, TrainingArguments

# Device check
if torch.cuda.is_available():
    print(f"CUDA available. Using GPU: {torch.cuda.get_device_name(0)}")
else:
    print("Warning: CUDA not available. Training will proceed on CPU. "
          "Install a CUDA-enabled torch package separately if you need GPU.")

from datasets import Dataset
from config import SYNTHESIZED_APPROVED_DIR, TRAIN_DATA_DIR, VAL_DATA_DIR

def load_pairs(root_dir: Path):
    pairs = []
    for num_dir in sorted(root_dir.iterdir()):
        if not num_dir.is_dir(): continue
        for txt in num_dir.glob("*_text.txt"):
            stem = txt.stem.replace("_text","")
            json_path = num_dir / f"{stem}_petri.json"
            if not json_path.exists(): continue
            text = txt.read_text(encoding="utf-8")
            petri = json.loads(json_path.read_text(encoding="utf-8"))
            pairs.append({"text": text, "petri_json": json.dumps(petri)})
    return pairs

def split_and_save(pairs, train_ratio=0.8):
    random.shuffle(pairs)
    cut = int(len(pairs)*train_ratio)
    for name, subset in [("train", pairs[:cut]), ("val", pairs[cut:])]:
        target = TRAIN_DATA_DIR if name=="train" else VAL_DATA_DIR
        for i, item in enumerate(subset):
            (target / f"{i:04d}.json").write_text(json.dumps(item), encoding="utf-8")

def semantic_loss(preds, labels):
    """
    Placeholder for graph-level Petri-net loss.
    E.g., compute structural similarity / isomorphism instead of raw token MSE.
    """
    # TODO: implement custom graph comparison
    return None

class PetriTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        outputs = model(**inputs)
        # default CE loss
        loss = super().compute_loss(model, inputs, return_outputs=False)
        # if you have logits -> decode and apply semantic_loss here
        # sem = semantic_loss(decoded_preds, decoded_labels)
        # combine: loss = loss + alpha*sem
        return (loss, outputs) if return_outputs else loss

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Salesforce/codet5-base",
                        help="CodeT5 model for JSON‐generation")
    parser.add_argument("--train_ratio", type=float, default=0.8)
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    # 1) load and split
    pairs = load_pairs(SYNTHESIZED_APPROVED_DIR)
    split_and_save(pairs, args.train_ratio)

    # 2) load into HuggingFace Dataset
    def load_ds(folder):
        files = list(Path(folder).glob("*.json"))
        data = [json.loads(f.read_text(encoding="utf-8")) for f in files]
        return Dataset.from_list(data)
    ds_train = load_ds(TRAIN_DATA_DIR)
    ds_val   = load_ds(VAL_DATA_DIR)

    # 3) tokenize
    tok = AutoTokenizer.from_pretrained(args.model)
    def preprocess(batch):
        # batch["text"] and batch["petri_json"] are lists
        inputs = ["generate_petri_json: " + t for t in batch["text"]]
        model_inputs = tok(
            inputs,
            truncation=True,
            padding="max_length",
            max_length=256
        )
        labels = tok(
            batch["petri_json"],
            truncation=True,
            padding="max_length",
            max_length=512
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    ds_train = ds_train.map(preprocess, batched=True)
    ds_val   = ds_val.map(preprocess, batched=True)

    # 4) model & trainer
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)
    training_args = TrainingArguments(
        output_dir="outputs/model_checkpoints",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        save_total_limit=2,
    )
    trainer = PetriTrainer(
        model=model, args=training_args,
        train_dataset=ds_train, eval_dataset=ds_val,
        tokenizer=tok
    )
    trainer.train()

if __name__=="__main__":
    main()
