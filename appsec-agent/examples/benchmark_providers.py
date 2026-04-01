from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from ollama import Client


REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")


BAD_CODE = """def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)
"""


SAFE_CODE = """def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))
"""


PROMPT_TEMPLATE = """You are evaluating Python code for SQL injection risk.
Return JSON only with this exact schema:
{{
  "vuln_found": boolean,
  "vuln_type": string,
  "confidence": number,
  "explanation": string
}}

Rules:
- If the code uses a parameterized query correctly, set "vuln_found" to false and "vuln_type" to "".
- If the code concatenates user input into SQL, set "vuln_found" to true and use "SQL Injection".
- Do not include markdown fences.

Code:
{code}
"""


@dataclass
class BenchmarkCase:
    name: str
    code: str
    expected_vuln_found: bool


@dataclass
class TrialResult:
    provider: str
    case_name: str
    latency_seconds: float
    success: bool
    parsed: bool
    vuln_found: bool | None
    vuln_type: str | None
    confidence: float | None
    explanation: str | None
    raw_text: str
    error: str = ""

    @property
    def quality_pass(self) -> bool:
        return self.success and self.parsed


def _nvidia_request(
    *,
    api_key: str,
    model: str,
    prompt: str,
    timeout_seconds: float,
) -> tuple[str, float]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "top_p": 0.7,
        "max_tokens": 512,
    }
    req = urllib.request.Request(
        url="https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    latency = time.perf_counter() - start
    content = payload["choices"][0]["message"]["content"]
    return content, latency


def _ollama_request(
    *,
    host: str | None,
    model: str,
    prompt: str,
    timeout_seconds: float,
) -> tuple[str, float]:
    client = Client(host=host, timeout=timeout_seconds)
    start = time.perf_counter()
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    latency = time.perf_counter() - start
    return response.message.content, latency


def _parse_trial_result(
    *,
    provider: str,
    case_name: str,
    raw_text: str,
    latency_seconds: float,
) -> TrialResult:
    try:
        payload = json.loads(raw_text)
    except Exception as exc:
        return TrialResult(
            provider=provider,
            case_name=case_name,
            latency_seconds=latency_seconds,
            success=False,
            parsed=False,
            vuln_found=None,
            vuln_type=None,
            confidence=None,
            explanation=None,
            raw_text=raw_text,
            error=f"invalid json: {exc}",
        )

    vuln_found = payload.get("vuln_found")
    vuln_type = payload.get("vuln_type")
    confidence = payload.get("confidence")
    explanation = payload.get("explanation")
    parsed = isinstance(vuln_found, bool) and isinstance(vuln_type, str)

    return TrialResult(
        provider=provider,
        case_name=case_name,
        latency_seconds=latency_seconds,
        success=parsed,
        parsed=parsed,
        vuln_found=vuln_found if isinstance(vuln_found, bool) else None,
        vuln_type=vuln_type if isinstance(vuln_type, str) else None,
        confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
        explanation=explanation if isinstance(explanation, str) else None,
        raw_text=raw_text,
        error="" if parsed else "missing required fields",
    )


def _evaluate_case(result: TrialResult, case: BenchmarkCase) -> bool:
    if not result.success or result.vuln_found is None:
        return False
    if result.vuln_found != case.expected_vuln_found:
        return False
    if case.expected_vuln_found:
        return bool(result.vuln_type) and "sql" in result.vuln_type.lower()
    return result.vuln_type in ("", None)


def _run_benchmarks(
    *,
    runs: int,
    timeout_seconds: float,
    ollama_model: str,
    nvidia_model: str,
) -> list[TrialResult]:
    cases = [
        BenchmarkCase(name="bad_sql_concat", code=BAD_CODE, expected_vuln_found=True),
        BenchmarkCase(name="safe_parameterized", code=SAFE_CODE, expected_vuln_found=False),
    ]

    nvidia_api_key = os.getenv("GEM29b_api_key") or os.getenv("NVIDIA_API_KEY")
    ollama_host = os.getenv("OLLAMA_HOST") or None
    results: list[TrialResult] = []

    for case in cases:
        prompt = PROMPT_TEMPLATE.format(code=case.code)
        for _ in range(runs):
            try:
                raw_text, latency = _ollama_request(
                    host=ollama_host,
                    model=ollama_model,
                    prompt=prompt,
                    timeout_seconds=timeout_seconds,
                )
                results.append(
                    _parse_trial_result(
                        provider="ollama",
                        case_name=case.name,
                        raw_text=raw_text,
                        latency_seconds=latency,
                    )
                )
            except Exception as exc:
                results.append(
                    TrialResult(
                        provider="ollama",
                        case_name=case.name,
                        latency_seconds=0.0,
                        success=False,
                        parsed=False,
                        vuln_found=None,
                        vuln_type=None,
                        confidence=None,
                        explanation=None,
                        raw_text="",
                        error=str(exc),
                    )
                )

            if not nvidia_api_key:
                results.append(
                    TrialResult(
                        provider="nvidia",
                        case_name=case.name,
                        latency_seconds=0.0,
                        success=False,
                        parsed=False,
                        vuln_found=None,
                        vuln_type=None,
                        confidence=None,
                        explanation=None,
                        raw_text="",
                        error="missing GEM29b_api_key or NVIDIA_API_KEY",
                    )
                )
                continue

            try:
                raw_text, latency = _nvidia_request(
                    api_key=nvidia_api_key,
                    model=nvidia_model,
                    prompt=prompt,
                    timeout_seconds=timeout_seconds,
                )
                results.append(
                    _parse_trial_result(
                        provider="nvidia",
                        case_name=case.name,
                        raw_text=raw_text,
                        latency_seconds=latency,
                    )
                )
            except urllib.error.HTTPError as exc:
                results.append(
                    TrialResult(
                        provider="nvidia",
                        case_name=case.name,
                        latency_seconds=0.0,
                        success=False,
                        parsed=False,
                        vuln_found=None,
                        vuln_type=None,
                        confidence=None,
                        explanation=None,
                        raw_text="",
                        error=f"http {exc.code}: {exc.reason}",
                    )
                )
            except Exception as exc:
                results.append(
                    TrialResult(
                        provider="nvidia",
                        case_name=case.name,
                        latency_seconds=0.0,
                        success=False,
                        parsed=False,
                        vuln_found=None,
                        vuln_type=None,
                        confidence=None,
                        explanation=None,
                        raw_text="",
                        error=str(exc),
                    )
                )
    return results


def _print_summary(results: list[TrialResult]) -> int:
    grouped: dict[str, list[TrialResult]] = {}
    for result in results:
        grouped.setdefault(result.provider, []).append(result)

    print("\nBenchmark summary\n")
    exit_code = 0
    for provider, provider_results in grouped.items():
        latencies = [r.latency_seconds for r in provider_results if r.latency_seconds > 0]
        success_count = sum(1 for r in provider_results if r.success)
        errors = [r for r in provider_results if r.error]
        case_expectations = {
            "bad_sql_concat": True,
            "safe_parameterized": False,
        }
        quality_passes = sum(
            1
            for r in provider_results
            if _evaluate_case(
                r,
                BenchmarkCase(
                    name=r.case_name,
                    code="",
                    expected_vuln_found=case_expectations[r.case_name],
                ),
            )
        )

        print(f"{provider.upper()}:")
        if latencies:
            print(
                f"  avg latency: {statistics.mean(latencies):.2f}s | "
                f"median latency: {statistics.median(latencies):.2f}s"
            )
        else:
            print("  avg latency: n/a")
        print(f"  parsed successes: {success_count}/{len(provider_results)}")
        print(f"  quality passes: {quality_passes}/{len(provider_results)}")
        if errors:
            print("  errors:")
            for error_result in errors[:3]:
                print(f"    - {error_result.case_name}: {error_result.error}")
            exit_code = 1
        print("  sample outputs:")
        for sample in provider_results[:2]:
            print(
                f"    - {sample.case_name}: vuln_found={sample.vuln_found} "
                f"vuln_type={sample.vuln_type!r} latency={sample.latency_seconds:.2f}s"
            )
        print()

    faster = _winner_by_speed(grouped)
    better = _winner_by_quality(grouped)
    if faster:
        print(f"Faster provider: {faster}")
    if better:
        print(f"Better provider on this benchmark: {better}")

    return exit_code


def _winner_by_speed(grouped: dict[str, list[TrialResult]]) -> str | None:
    averages: dict[str, float] = {}
    for provider, items in grouped.items():
        latencies = [r.latency_seconds for r in items if r.latency_seconds > 0]
        if latencies:
            averages[provider] = statistics.mean(latencies)
    if len(averages) < 2:
        return None
    return min(averages, key=averages.get)


def _winner_by_quality(grouped: dict[str, list[TrialResult]]) -> str | None:
    case_expectations = {
        "bad_sql_concat": True,
        "safe_parameterized": False,
    }
    scores: dict[str, int] = {}
    for provider, items in grouped.items():
        scores[provider] = sum(
            1
            for r in items
            if _evaluate_case(
                r,
                BenchmarkCase(
                    name=r.case_name,
                    code="",
                    expected_vuln_found=case_expectations[r.case_name],
                ),
            )
        )
    if len(scores) < 2:
        return None
    return max(scores, key=scores.get)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Ollama vs NVIDIA-hosted Gemma.")
    parser.add_argument("--runs", type=int, default=2, help="Number of runs per case/provider.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds.")
    parser.add_argument("--ollama-model", default="llama3.1:8b", help="Ollama model to benchmark.")
    parser.add_argument(
        "--nvidia-model",
        default="google/gemma-2-9b-it",
        help="NVIDIA hosted model to benchmark.",
    )
    args = parser.parse_args()

    results = _run_benchmarks(
        runs=max(1, args.runs),
        timeout_seconds=args.timeout,
        ollama_model=args.ollama_model,
        nvidia_model=args.nvidia_model,
    )
    return _print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
