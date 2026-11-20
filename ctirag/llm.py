"""LLM client: Groq with on-disk cache, shared rate limiter, retries and token accounting.

A MockLLM with the same interface lets the full pipeline be tested without an API key.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sqlite3
import threading
import time
from pathlib import Path

from .config import GROQ_MODEL_PREFERENCE, Config


class DailyLimitReached(RuntimeError):
    """Raised when the provider's daily quota is exhausted; runs can be resumed later."""


def parse_json(text: str) -> dict:
    """Best-effort JSON extraction from model output."""
    if not text:
        return {}
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:  # noqa: BLE001
            pass
    return {}


class _Cache:
    def __init__(self, path: Path):
        self.lock = threading.Lock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS c (k TEXT PRIMARY KEY, v TEXT)")
        self.db.commit()

    def get(self, k):
        with self.lock:
            r = self.db.execute("SELECT v FROM c WHERE k=?", (k,)).fetchone()
        return json.loads(r[0]) if r else None

    def put(self, k, v):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO c VALUES (?,?)", (k, json.dumps(v)))
            self.db.commit()


class _RateLimiter:
    def __init__(self, rpm: int):
        self.interval = 60.0 / max(rpm, 1)
        self.lock = threading.Lock()
        self.next = 0.0

    def wait(self):
        with self.lock:
            now = time.time()
            t = max(now, self.next)
            self.next = t + self.interval
        if t > now:
            time.sleep(t - now)


class BaseLLM:
    model = "base"

    def __init__(self, cfg: Config):
        self.cfg = cfg
        cfg.ensure()
        self.cache = _Cache(cfg.work_dir and Path(cfg.work_dir) / "llm_cache.sqlite")

    def _key(self, messages, json_mode):
        # the repeat index is part of the key, so repeat 1, 2, ... are genuine new samples, not cache hits
        s = json.dumps([self.model, messages, json_mode, self.cfg.temperature, self.cfg.max_tokens,
                        self.cfg.repeat], sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()

    def chat(self, messages: list[dict], task: str = "", json_mode: bool = True, tracker: dict | None = None) -> str:
        k = self._key(messages, json_mode)
        hit = self.cache.get(k)
        t0 = time.time()
        if hit is None:
            text, usage = self._call(messages, task, json_mode)
            hit = {"text": text, "usage": usage}
            self.cache.put(k, hit)
            cached = False
        else:
            cached = True
        if tracker is not None:
            tracker["calls"] = tracker.get("calls", 0) + 1
            tracker["prompt_tokens"] = tracker.get("prompt_tokens", 0) + hit["usage"].get("prompt_tokens", 0)
            tracker["completion_tokens"] = tracker.get("completion_tokens", 0) + hit["usage"].get("completion_tokens", 0)
            tracker["cached_calls"] = tracker.get("cached_calls", 0) + int(cached)
            tracker["llm_seconds"] = tracker.get("llm_seconds", 0.0) + (hit["usage"].get("seconds", 0.0))
            tracker.setdefault("tasks", []).append(task)
        return hit["text"]

    def json(self, messages, task="", tracker=None) -> dict:
        out = parse_json(self.chat(messages, task, True, tracker))
        return out if isinstance(out, dict) else {}

    def _call(self, messages, task, json_mode):  # pragma: no cover
        raise NotImplementedError


class GroqLLM(BaseLLM):
    def __init__(self, cfg: Config, api_key: str | None = None):
        from groq import Groq
        self.client = Groq(api_key=api_key, max_retries=0)
        self.limiter = _RateLimiter(cfg.requests_per_minute)
        self.model = cfg.llm_model or self.pick_model()
        super().__init__(cfg)
        print(f"[llm] using Groq model: {self.model}")

    def pick_model(self) -> str:
        try:
            avail = {m.id for m in self.client.models.list().data}
        except Exception as e:  # noqa: BLE001
            print(f"[llm] could not list models ({e}); defaulting to {GROQ_MODEL_PREFERENCE[0]}")
            return GROQ_MODEL_PREFERENCE[0]
        for m in GROQ_MODEL_PREFERENCE:
            if m in avail:
                return m
        raise RuntimeError(f"None of {GROQ_MODEL_PREFERENCE} available. Available: {sorted(avail)}")

    def _call(self, messages, task, json_mode):
        import groq
        kwargs = dict(model=self.model, messages=messages, temperature=self.cfg.temperature,
                      max_tokens=self.cfg.max_tokens, seed=1000 + self.cfg.repeat)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if self.model.startswith("openai/gpt-oss"):
            kwargs["reasoning_effort"] = "low"
            kwargs["max_tokens"] = self.cfg.max_tokens * 3
        delay = 5.0
        for attempt in range(8):
            self.limiter.wait()
            t0 = time.time()
            try:
                r = self.client.chat.completions.create(**kwargs)
                u = r.usage
                return (r.choices[0].message.content or "",
                        {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens,
                         "seconds": time.time() - t0})
            except groq.RateLimitError as e:
                msg = str(e)
                if "per day" in msg or "TPD" in msg or "RPD" in msg:
                    m = re.search(r"try again in ([\d.]+)m", msg)
                    if m and float(m.group(1)) < 15:
                        time.sleep(float(m.group(1)) * 60 + 5)
                        continue
                    raise DailyLimitReached(msg) from e
                ra = None
                try:
                    ra = float(e.response.headers.get("retry-after"))
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(ra or delay)
                delay = min(delay * 2, 120)
            except groq.BadRequestError as e:
                # JSON mode can fail validation when the model emits malformed JSON: retry without it.
                if "json" in str(e).lower() and "response_format" in kwargs:
                    kwargs.pop("response_format")
                    continue
                if "reasoning_effort" in str(e) and "reasoning_effort" in kwargs:
                    kwargs.pop("reasoning_effort")
                    continue
                if "seed" in str(e) and "seed" in kwargs:
                    kwargs.pop("seed")
                    continue
                raise
            except (groq.APIConnectionError, groq.InternalServerError, groq.APITimeoutError):
                time.sleep(delay)
                delay = min(delay * 2, 120)
        raise RuntimeError("Groq call failed after retries")


class MockLLM(BaseLLM):
    """Deterministic heuristic stand-in for pipeline tests (no network).

    It reads identifiers from the evidence block, so systems produce non-trivial,
    comparable outputs; numbers from the mock are NOT research results.
    """
    model = "mock-heuristic"

    def __init__(self, cfg: Config):
        super().__init__(cfg)
        self.rng = random.Random(0)

    @staticmethod
    def _section(prompt: str, name: str) -> str:
        m = re.search(rf"<{name}>(.*?)</{name}>", prompt, re.S)
        return m.group(1) if m else ""

    def _call(self, messages, task, json_mode):
        from .corpus import extract_ids
        prompt = messages[-1]["content"]
        q = self._section(prompt, "question")
        ev = self._section(prompt, "evidence")
        qids = extract_ids(q)
        want = "mitigation" if "M-ID" in q or "mitigations (M" in q else (
            "control" if "800-53" in q else ("technique" if "ATT&CK" in q else None))
        ev_ids = [i for i in extract_ids(ev, (want,) if want else None) if i not in qids]
        usage = {"prompt_tokens": len(prompt) // 4, "completion_tokens": 60, "seconds": 0.0}
        if task in ("hop", "agent_step"):
            if task == "agent_step" and "<step>0</step>" in prompt:
                ids = extract_ids(ev, ("cwe", "capec"))[:2]
                acts = [{"action": "lookup", "id": i} for i in ids] or [{"action": "finish"}]
                return json.dumps({"actions": acts}), usage
            if task == "hop" and "Hop 1" not in prompt:
                nxt = extract_ids(ev, ("cwe", "capec"))
                return json.dumps({"done": not nxt, "next_query": " ".join(nxt[:2]) or q[:80]}), usage
            return json.dumps({"done": True, "actions": [{"action": "finish"}]}), usage
        if task == "grade":
            ids = re.findall(r"^\[([^\]]+)\]", ev, re.M)
            rel = [i for i in ids if any(x in ev.split(f"[{i}]")[1][:600] for x in qids)] or ids[:3]
            return json.dumps({"relevant": rel, "overall": "CORRECT" if rel else "INCORRECT"}), usage
        if task == "rewrite":
            return json.dumps({"queries": [q[:120]]}), usage
        if task == "entail":
            n = len(re.findall(r"^\d+\.", self._section(prompt, "claims"), re.M))
            return json.dumps({"results": [{"supported": self.rng.random() < 0.5} for _ in range(n)]}), usage
        # answer / draft
        picks = ev_ids[: self.rng.randint(1, 5)]
        verdict = None
        if "Verify the following claim" in q:
            verdict = "SUPPORTED" if qids and qids[-1] in extract_ids(ev) and self.rng.random() < 0.8 else (
                "NOT_ENOUGH_INFO" if not ev_ids else "UNSUPPORTED")
        claims = []
        if task == "draft" and qids:
            claims = [{"subject": qids[0], "object": p, "relation": "", "citations": []} for p in picks]
            if verdict and len(qids) >= 2:
                claims = [{"subject": qids[-1] if "mitigation M" in q else qids[0],
                           "object": qids[0] if "mitigation M" in q else qids[-1], "relation": "", "citations": []}]
        return json.dumps({"answer": f"Mock answer: {', '.join(picks)}", "ids": picks, "verdict": verdict,
                           "flags": [], "citations": [], "claims": claims,
                           "focus_entity": qids[0] if qids else None, "target_type": want}), usage


def make_llm(cfg: Config, api_key: str | None = None) -> BaseLLM:
    if cfg.llm_provider == "mock":
        return MockLLM(cfg)
    return GroqLLM(cfg, api_key)
