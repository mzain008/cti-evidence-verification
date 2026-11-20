"""Hybrid retriever: BM25 + dense embeddings fused with reciprocal-rank fusion.

Dense side uses sentence-transformers when available (Colab GPU) and falls back to
TF-IDF cosine so that the whole pipeline also runs on CPU-only machines.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from .corpus import Corpus, Doc, extract_ids

_TOK = re.compile(r"[a-z0-9]+(?:[.\-()][a-z0-9]+)*")
STOP = set("the a an of and or to in for on by with is are be as at from that this which may can its it into".split())


def tokenize(t: str) -> list[str]:
    toks = _TOK.findall((t or "").lower())
    return [x for x in toks if x not in STOP]


class HybridIndex:
    def __init__(self, corpus: Corpus, dense_model: str | None = None, cache_dir: Path | None = None):
        self.corpus = corpus
        self.ids = list(corpus.docs.keys())
        self.pos = {d: i for i, d in enumerate(self.ids)}
        self.texts = [f"{corpus.docs[i].title}. {corpus.docs[i].text}" for i in self.ids]
        self.bm25 = BM25Okapi([tokenize(t) for t in self.texts])
        self.dense_kind = None
        self._init_dense(dense_model, cache_dir)

    # -- dense ---------------------------------------------------------------
    def _init_dense(self, model_name, cache_dir):
        if model_name:
            try:
                from sentence_transformers import SentenceTransformer
                self.st = SentenceTransformer(model_name)
                key = hashlib.md5(("|".join(self.ids) + model_name).encode()).hexdigest()[:12]
                cache = Path(cache_dir) / f"emb_{key}.npy" if cache_dir else None
                if cache and cache.exists():
                    self.emb = np.load(cache)
                else:
                    self.emb = self.st.encode(self.texts, batch_size=64, normalize_embeddings=True,
                                              show_progress_bar=True, convert_to_numpy=True)
                    if cache:
                        np.save(cache, self.emb)
                self.dense_kind = f"st:{model_name}"
                return
            except Exception as e:  # noqa: BLE001
                print(f"[index] sentence-transformers unavailable ({e}); using TF-IDF dense fallback")
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.tfidf = TfidfVectorizer(tokenizer=tokenize, lowercase=False, sublinear_tf=True,
                                     min_df=1, max_features=200_000, token_pattern=None)
        self.tfm = self.tfidf.fit_transform(self.texts)
        self.dense_kind = "tfidf"

    def _dense_scores(self, query: str) -> np.ndarray:
        if self.dense_kind and self.dense_kind.startswith("st:"):
            q = self.st.encode(["Represent this sentence for searching relevant passages: " + query],
                               normalize_embeddings=True, convert_to_numpy=True)[0]
            return self.emb @ q
        q = self.tfidf.transform([query])
        return (self.tfm @ q.T).toarray().ravel()

    # -- search ----------------------------------------------------------------
    def search(self, query: str, k: int = 8, sources: list[str] | None = None,
               id_boost: bool = True, rrf_k: int = 60) -> list[tuple[Doc, float]]:
        bm = self.bm25.get_scores(tokenize(query))
        de = self._dense_scores(query)
        score = np.zeros(len(self.ids))
        for arr in (bm, de):
            order = np.argsort(-arr)
            ranks = np.empty_like(order)
            ranks[order] = np.arange(len(order))
            score += 1.0 / (rrf_k + ranks + 1)
        if id_boost:
            for eid in extract_ids(query):
                for did in self.corpus.by_entity.get(eid, []):
                    if did in self.pos:
                        score[self.pos[did]] += 1.0  # exact identifier match goes first
        order = np.argsort(-score)
        out = []
        for j in order:
            d = self.corpus.docs[self.ids[j]]
            if sources and d.source not in sources:
                continue
            out.append((d, float(score[j])))
            if len(out) >= k:
                break
        return out
