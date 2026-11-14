import os
import re
from pathlib import Path

import numpy as np

from netops_agent.config import RUNBOOKS_DIR

_model = None
MODEL_CACHE = Path(__file__).resolve().parent.parent.parent / "models_cache"


def _vendor_dir(vendor: str) -> Path:
    path = RUNBOOKS_DIR / vendor.lower()
    if not path.is_dir():
        raise LookupError(f"No runbooks for vendor '{vendor}'")
    return path


def list_runbooks(vendor: str) -> list[str]:
    """Runbook names (without .md) for one vendor."""
    return sorted(p.stem for p in _vendor_dir(vendor).glob("*.md"))


def get_runbook(name: str, vendor: str) -> str:
    path = _vendor_dir(vendor) / f"{name}.md"
    if not path.exists():
        raise LookupError(f"Runbook '{name}' not found for vendor '{vendor}'")
    return path.read_text()


def get_steps(name: str, interface: str, vendor: str) -> dict:
    """Copy the numbered steps out of a runbook exactly as written (no LLM)."""
    remote, onsite, current = [], [], None
    for line in get_runbook(name, vendor).splitlines():
        if line.startswith("## NOC Remote"):
            current = remote
        elif line.startswith("## On-Site"):
            current = onsite
        elif current is not None and re.match(r"\d+\.\s", line):
            step = re.sub(r"^\d+\.\s*", "", line).replace("`", "")
            current.append(step.replace("<interface>", interface))
    return {"remote_steps": remote, "onsite_steps": onsite}


def _embed(texts: list[str]) -> np.ndarray:
    global _model
    if _model is None:
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        from fastembed import TextEmbedding

        _model = TextEmbedding("BAAI/bge-small-en-v1.5", cache_dir=str(MODEL_CACHE))
    return np.array(list(_model.embed(texts)))


def _keyword_scores(query: str, docs: list[str]) -> list[float]:
    q = set(re.findall(r"[a-z0-9]+", query.lower()))
    scores = []
    for d in docs:
        words = set(re.findall(r"[a-z0-9]+", d.lower()))
        scores.append(len(q & words) / (len(q) or 1))
    return scores


def search_runbooks(query: str, vendor: str, k: int = 2) -> list[tuple[str, float]]:
    """Best k runbooks for this vendor, as (name, score). Vendor is a filter applied first."""
    names = list_runbooks(vendor)
    # Search on the title + Symptoms part only, not on the commands.
    docs = [get_runbook(n, vendor).split("## NOC")[0] for n in names]
    try:
        doc_vecs = _embed(docs)
        q_vec = _embed([query])[0]
        sims = doc_vecs @ q_vec / (np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(q_vec))
        scores = [float(s) for s in sims]
    except Exception as e:
        print(f"[rag] embeddings unavailable ({e}); using keyword match instead")
        scores = _keyword_scores(query, docs)
    ranked = sorted(zip(names, scores), key=lambda x: x[1], reverse=True)
    return ranked[:k]
