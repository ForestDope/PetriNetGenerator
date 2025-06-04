# Petri Net Generation from Multimedia Scenarios

This project aims to generate JSON-based data structures that can be algorithmically transformed into Petri nets. The goal is to convert text descriptions of multimedia scenarios—such as slides containing text, videos, audio, buttons, etc.—into structured JSON suitable for Petri net creation.

## Overview

- **Input:** A text description outlining components of a multimedia scenario.
- **Output:** A JSON structure representing a Petri net, including places, transitions, and arcs.

## Approach

1. **Dataset Preparation:**  
   - Create a dataset of paired examples where each example consists of an input text and its corresponding JSON output.
   - Use formats such as JSON or JSON Lines (JSONL) for ease of use with machine learning frameworks.

2. **Model Selection:**  
   - Fine-tune existing LLMs (e.g., LLaMA 3.2 3B) using frameworks like Hugging Face Transformers.
   - Consider parameter-efficient fine-tuning methods (e.g., LoRA) or generating synthetic examples with another LLM.

3. **Training Framework:**  
   - Utilize Hugging Face Transformers and the Trainer API.
   - Employ the Hugging Face Datasets library for handling JSON/JSONL data.
   - Leverage PyTorch for model training with GPU support (e.g., on a 6GB VRAM card).

## File Structure

```plaintext
project-root/
├── data/
│   ├── train.jsonl         # Training data examples
│   └── val.jsonl           # Validation data examples
├── notebooks/
│   └── exploration.ipynb   # Data exploration and experiment scripts
├── src/
│   ├── main.py             # Main training script
│   ├── model_utils.py      # Helper functions for model loading and tokenization
│   └── config.py           # Configuration settings (e.g., training parameters)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Getting Started

1. **Install Dependencies:**

   ```bash
   pip install transformers datasets torch
   ```

2. **Prepare Your Data:**  
   Place your training and validation data in the `data/` directory as JSONL files.

3. **Fine-Tuning:**  
   Run the main training script from the `src/` directory:

   ```bash
   python src/main.py
   ```

## Next Steps

- Experiment with different model sizes and fine-tuning techniques.
- Augment or generate synthetic training data with another LLM.
- Explore parameter-efficient methods if you're constrained by GPU VRAM.

## License

[Specify your license here]

## Acknowledgments

- Hugging Face Transformers and Datasets
- The open-source community for LLM research and development
