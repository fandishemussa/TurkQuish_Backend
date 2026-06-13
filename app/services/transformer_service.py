from __future__ import annotations
import json
import math
import time
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from app.core.config import get_settings

settings = get_settings()

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover
    torch = None
    nn = None


class PositionalEncoding(nn.Module):  # type: ignore[misc]
    def __init__(self, d_model: int, max_len: int = 256):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, : x.size(1)]


class URLTransformer(nn.Module):  # type: ignore[misc]
    def __init__(self, vocab: int, n_classes: int, d: int = 64, heads: int = 4, layers: int = 3, d_ff: int = 128, drop: float = 0.1, pad_idx: int = 0, max_len: int = 256):
        super().__init__()
        self.pad_idx = pad_idx
        self.d_model = d
        self.embed = nn.Embedding(vocab, d, padding_idx=pad_idx)
        self.pos = PositionalEncoding(d, max_len=max_len)
        enc = nn.TransformerEncoderLayer(d, heads, d_ff, drop, activation="gelu", batch_first=True)
        self.encoder = nn.TransformerEncoder(enc, layers)
        self.dropout = nn.Dropout(drop)
        self.head = nn.Sequential(nn.Linear(d * 2, d), nn.GELU(), nn.Dropout(drop), nn.Linear(d, n_classes))

    def forward(self, x):
        mask = x == self.pad_idx
        h = self.pos(self.embed(x) * math.sqrt(self.d_model))
        h = self.encoder(h, src_key_padding_mask=mask)
        hm = h.masked_fill(mask.unsqueeze(-1), 0).sum(1) / (~mask).sum(1, keepdim=True).clamp(min=1)
        hx = h.masked_fill(mask.unsqueeze(-1), -1e9).max(1).values
        return self.head(self.dropout(torch.cat([hm, hx], 1)))


class URLTransformerService:
    def __init__(self) -> None:
        self.available = False
        self.model = None
        self.char2idx: Dict[str, int] = {}
        self.labels: list[str] = []
        self.max_len = 256
        self.pad_idx = 0
        self.unk_idx = 1
        self.device = "cpu"
        self.version = "not-loaded"

    def load(self, artifact_dir: Path) -> "URLTransformerService":
        if torch is None or nn is None or not settings.enable_url_transformer:
            return self

        root = artifact_dir / "url_transformer"
        model_path = root / "url_transformer.pt"
        vocab_path = root / "char_vocab.json"
        config_path = root / "transformer_config.json"
        label_path = root / "label_encoder.json"

        if not (model_path.exists() and vocab_path.exists() and config_path.exists()):
            return self

        with vocab_path.open("r", encoding="utf-8") as f:
            vocab_obj = json.load(f)
        self.char2idx = vocab_obj.get("char2idx", vocab_obj)
        self.pad_idx = int(vocab_obj.get("pad_idx", self.char2idx.get("<PAD>", 0)))
        self.unk_idx = int(vocab_obj.get("unk_idx", self.char2idx.get("<UNK>", 1)))

        with config_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.max_len = int(cfg.get("max_len", 256))
        n_classes = int(cfg.get("n_classes", 5))
        d = int(cfg.get("embed_dim", cfg.get("d_model", 64)))
        heads = int(cfg.get("heads", 4))
        layers = int(cfg.get("layers", 3))
        d_ff = int(cfg.get("d_ff", 128))
        drop = float(cfg.get("dropout", 0.1))
        self.version = str(cfg.get("model_version", "url-transformer-v1"))

        if label_path.exists():
            with label_path.open("r", encoding="utf-8") as f:
                labels_obj = json.load(f)
            self.labels = labels_obj.get("model_classes_label_order") or labels_obj.get("classes") or []
        if not self.labels:
            self.labels = ["benign", "phishing", "malware", "scam", "other_malicious"][:n_classes]

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = URLTransformer(
            vocab=len(self.char2idx), n_classes=n_classes, d=d, heads=heads,
            layers=layers, d_ff=d_ff, drop=drop, pad_idx=self.pad_idx, max_len=self.max_len
        ).to(self.device)
        state = torch.load(model_path, map_location=self.device)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        self.model.load_state_dict(state)
        self.model.eval()
        self.available = True
        return self

    def _encode(self, url: str):
        url = str(url).lower()[: self.max_len]
        ids = [self.char2idx.get(c, self.unk_idx) for c in url]
        ids += [self.pad_idx] * (self.max_len - len(ids))
        return torch.tensor([ids], dtype=torch.long, device=self.device)

    def predict_proba(self, url: str) -> Optional[Dict[str, float]]:
        probs, _ = self.predict_proba_with_timing(url)
        return probs

    def predict_proba_with_timing(self, url: str) -> tuple[Optional[Dict[str, float]], Dict[str, float]]:
        timing_ms: Dict[str, float] = {}
        if not self.available or self.model is None or torch is None:
            return None, timing_ms

        t = time.perf_counter()
        encoded = self._encode(url)
        timing_ms["url_transformer_tokenization"] = round((time.perf_counter() - t) * 1000, 4)

        t = time.perf_counter()
        with torch.no_grad():
            logits = self.model(encoded)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        timing_ms["url_transformer_inference"] = round((time.perf_counter() - t) * 1000, 4)
        return {self.labels[i]: float(probs[i]) for i in range(min(len(self.labels), len(probs)))}, timing_ms


url_transformer_service = URLTransformerService()

