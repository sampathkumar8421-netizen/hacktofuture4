"""
Lily02 Execution Engine (Decoupled from Reasoning)
===================================================
This module handles ALL deterministic execution logic:
- Async chunk parallelization via asyncio.gather()
- Automatic retries with exponential backoff
- Result caching across identical chunk calls
- Tool-loop guards (max iteration limits)

The Orchestrator (reasoning layer) ONLY produces a plan.
This engine ONLY executes that plan. The two never mix.
"""

import asyncio
import time
import hashlib
import json
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor

from hyperpipeline.schemas import ApplicationSpec, ExecutionPlan


# ---------------------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------------------
MAX_TOOL_CALLS = 8          # Hard limit on chunk executions per request
MAX_RETRIES = 2             # Retries per chunk before failing gracefully
RETRY_BACKOFF_SEC = 0.5     # Base backoff between retries
CACHE_TTL_SEC = 300         # 5 minute cache TTL for identical chunk results


class ExecutionCache:
    """Simple in-memory TTL cache for chunk results."""
    def __init__(self):
        self._store: Dict[str, tuple] = {}  # key -> (result, timestamp)

    def _make_key(self, chunk_name: str, spec: ApplicationSpec) -> str:
        raw = f"{chunk_name}:{spec.application_type}:{spec.required_variables}:{spec.derived_indicators}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, chunk_name: str, spec: ApplicationSpec):
        key = self._make_key(chunk_name, spec)
        if key in self._store:
            result, ts = self._store[key]
            if time.time() - ts < CACHE_TTL_SEC:
                print(f"  [Cache HIT] {chunk_name} -> serving from cache")
                return result
            else:
                del self._store[key]
        return None

    def set(self, chunk_name: str, spec: ApplicationSpec, result):
        key = self._make_key(chunk_name, spec)
        self._store[key] = (result, time.time())


# Singleton cache instance
_cache = ExecutionCache()


class ExecutionEngine:
    """
    Deterministic execution layer. Receives a plan from the reasoning layer
    and executes it with parallelization, retries, caching, and guards.
    """

    def __init__(self, chunks_map: dict):
        self.chunks_map = chunks_map
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _run_chunk_sync(self, chunk_name: str, spec: ApplicationSpec, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single chunk with retry logic."""
        cached = _cache.get(chunk_name, spec)
        if cached is not None:
            context.update(cached)
            return context

        chunk = self.chunks_map.get(chunk_name)
        if chunk is None:
            print(f"  [Skip] Chunk '{chunk_name}' not found in registry.")
            return context

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = chunk.execute(spec, context.copy())
                # Cache the delta (new keys added by this chunk)
                delta = {k: v for k, v in result.items() if k not in context or context[k] != v}
                _cache.set(chunk_name, spec, delta)
                return result
            except Exception as e:
                last_error = e
                wait = RETRY_BACKOFF_SEC * attempt
                print(f"  [Retry {attempt}/{MAX_RETRIES}] {chunk_name} failed: {e}. Waiting {wait}s...")
                time.sleep(wait)

        print(f"  [FAIL] {chunk_name} exhausted retries. Last error: {last_error}")
        return context

    async def execute_plan(self, spec: ApplicationSpec, plan: ExecutionPlan, raw_query: str, uploaded_files: list = None) -> Dict[str, Any]:
        """
        Execute the plan with parallelization where possible.
        """
        context = {
            "raw_query": raw_query,
            "uploaded_files": uploaded_files or []
        }
        steps = plan.steps
        tool_call_count = 0

        # Classify steps into execution phases
        phase_1 = []   # Must run first (retrieval)
        phase_2 = []   # Can run in parallel (feature, domain)
        phase_3 = []   # Must run last (reporting)

        for step in steps:
            if tool_call_count >= MAX_TOOL_CALLS:
                print(f"  [GUARD] Tool loop limit reached ({MAX_TOOL_CALLS}). Stopping execution.")
                break

            if "retrieval" in step:
                phase_1.append(step)
            elif "reporting" in step or "evidence" in step:
                phase_3.append(step)
            else:
                phase_2.append(step)
            tool_call_count += 1

        # --- Phase 1: Sequential retrieval (data dependency) ---
        for step in phase_1:
            print(f"  [Phase 1 - Sequential] -> {step}")
            context = self._run_chunk_sync(step, spec, context)

        # --- Phase 2: Parallel feature/domain computation ---
        if len(phase_2) > 1:
            print(f"  [Phase 2 - Parallel] -> {phase_2}")
            loop = asyncio.get_event_loop()
            futures = []
            for step in phase_2:
                future = loop.run_in_executor(
                    self._executor,
                    self._run_chunk_sync,
                    step, spec, context.copy()
                )
                futures.append((step, future))

            results = await asyncio.gather(*[f for _, f in futures], return_exceptions=True)

            # Merge parallel results back into context
            for (step, _), result in zip(futures, results):
                if isinstance(result, Exception):
                    print(f"  [Parallel FAIL] {step}: {result}")
                elif isinstance(result, dict):
                    context.update(result)
        elif phase_2:
            for step in phase_2:
                print(f"  [Phase 2 - Sequential] -> {step}")
                context = self._run_chunk_sync(step, spec, context)

        # --- Phase 3: Sequential reporting (depends on all results) ---
        for step in phase_3:
            print(f"  [Phase 3 - Sequential] -> {step}")
            context = self._run_chunk_sync(step, spec, context)

        return context

    def get_execution_stats(self) -> dict:
        return {
            "max_tool_calls": MAX_TOOL_CALLS,
            "max_retries": MAX_RETRIES,
            "cache_entries": len(_cache._store),
            "cache_ttl_sec": CACHE_TTL_SEC
        }
