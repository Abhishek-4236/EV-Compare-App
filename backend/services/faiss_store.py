from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def _faiss() -> Any:
    import faiss
    return faiss


class FaissStore:
    def __init__(self, index: Any, id_map: list[str]):
        self.index = index
        self.id_map = id_map

    @classmethod
    def build(cls, vectors: list[list[float]], ids: list[str]) -> "FaissStore":
        if not vectors:
            raise ValueError("Cannot build FAISS store with no vectors")
        faiss = _faiss()
        matrix = np.array(vectors, dtype="float32")
        faiss.normalize_L2(matrix)
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        return cls(index=index, id_map=ids)

    def save(self, index_path: str | Path, meta_path: str | Path) -> None:
        faiss = _faiss()
        index_target = Path(index_path)
        meta_target = Path(meta_path)
        index_target.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_target))
        meta_target.write_text(json.dumps({"ids": self.id_map}, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, index_path: str | Path, meta_path: str | Path) -> "FaissStore":
        faiss = _faiss()
        index = faiss.read_index(str(index_path))
        metadata = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        return cls(index=index, id_map=metadata["ids"])

    def search(self, vector: list[float], top_k: int = 8) -> list[tuple[str, float]]:
        if self.index.ntotal == 0:
            return []
        faiss = _faiss()
        query = np.array([vector], dtype="float32")
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, top_k)
        results: list[tuple[str, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(self.id_map):
                continue
            results.append((self.id_map[idx], float(score)))
        return results
