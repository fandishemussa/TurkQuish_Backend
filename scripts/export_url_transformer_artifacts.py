"""
Run this inside the notebook/session where your trained URLTransformer exists.
It exports the optional backend fallback artifacts:

app/artifacts/url_transformer/
  url_transformer.pt
  char_vocab.json
  transformer_config.json
  label_encoder.json

You must update variable names below to match your notebook.
"""
from pathlib import Path
import json
import torch

ARTIFACT_DIR = Path("app/artifacts/url_transformer")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# CHANGE THESE to your notebook variables
model = url_transformer_model          # noqa: F821
char2idx = char2idx                    # noqa: F821
MAX_LEN = MAX_LEN                      # noqa: F821
EMBED_DIM = EMBED_DIM                  # noqa: F821
CLASS_NAMES = ["benign", "phishing", "malware", "scam", "other_malicious"]

# Save state dict only
model.eval()
torch.save(model.state_dict(), ARTIFACT_DIR / "url_transformer.pt")

with open(ARTIFACT_DIR / "char_vocab.json", "w", encoding="utf-8") as f:
    json.dump({"char2idx": char2idx, "pad_idx": 0, "unk_idx": 1}, f, indent=2, ensure_ascii=False)

with open(ARTIFACT_DIR / "transformer_config.json", "w", encoding="utf-8") as f:
    json.dump({
        "model_version": "url-transformer-5class-v1",
        "max_len": int(MAX_LEN),
        "n_classes": 5,
        "embed_dim": int(EMBED_DIM),
        "heads": 4,
        "layers": 3,
        "d_ff": 128,
        "dropout": 0.1
    }, f, indent=2)

with open(ARTIFACT_DIR / "label_encoder.json", "w", encoding="utf-8") as f:
    json.dump({"classes": CLASS_NAMES, "model_classes_label_order": CLASS_NAMES}, f, indent=2)

print("Exported URL-Transformer artifacts to", ARTIFACT_DIR)
