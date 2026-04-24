from __future__ import annotations

import json
import math
import time
from collections import defaultdict
from pathlib import Path
import sys

import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import settings
from services.ev_catalog import load_excel_as_documents

API_URL = "http://127.0.0.1:8000/api/chat/"
REPORT_DIR = Path(__file__).resolve().parents[1] / "reports"


def _find_vehicle(documents, needle: str):
    needle_lower = needle.lower()
    for doc in documents:
        if needle_lower in doc.name.lower():
            return doc
    raise ValueError(f"Vehicle containing '{needle}' not found in dataset")


def _kw(*parts: str) -> list[str]:
    return [part.lower() for part in parts if part]


def build_cases():
    documents = load_excel_as_documents(settings.EV_EXCEL_PATH)
    featured_names = [
        "Ola S1 Pro",
        "Ather 450X",
        "TVS iQube",
        "Bajaj Chetak",
        "Hero Vida V1",
        "Tata Nexon EV",
        "MG ZS EV",
        "Mahindra XUV400",
        "BYD Atto 3",
        "Hyundai Ioniq 5",
        "Kia EV6",
        "Tata Punch EV",
        "Tata Tiago EV",
        "MG Comet EV",
        "Mercedes EQS",
        "BYD Seal",
        "Ather Rizta Z",
        "Ola S1 X",
    ]
    vehicles = [_find_vehicle(documents, name) for name in featured_names]

    cases = []

    def add(difficulty, style, query, expected_keywords=None, expect_sources_min=0, mode="keywords"):
        cases.append({
            "id": len(cases) + 1,
            "difficulty": difficulty,
            "style": style,
            "query": query,
            "expected_keywords": expected_keywords or [],
            "expect_sources_min": expect_sources_min,
            "mode": mode,
        })

    # Easy: 25
    easy_queries = [
        ("What is the price of Ola S1 Pro?", _kw("ola", "s1 pro", "price"), 1),
        ("Tell me the range of Ather 450X.", _kw("ather", "450x", "range"), 1),
        ("Battery capacity of TVS iQube?", _kw("tvs", "iqube", "battery"), 1),
        ("What is the charging time of Bajaj Chetak?", _kw("bajaj", "chetak", "charging"), 1),
        ("How much does Hero Vida V1 cost?", _kw("hero", "vida", "price"), 1),
        ("Tata Nexon EV price and range", _kw("nexon", "price", "range"), 1),
        ("MG ZS EV battery details", _kw("mg", "zs", "battery"), 1),
        ("Mahindra XUV400 charging type", _kw("mahindra", "xuv400", "charging"), 1),
        ("Range of BYD Atto 3?", _kw("byd", "atto", "range"), 1),
        ("What is the price of Hyundai Ioniq 5?", _kw("hyundai", "ioniq", "price"), 1),
        ("Kia EV6 battery and charging time", _kw("kia", "ev6", "battery", "charging"), 1),
        ("Give me Tata Punch EV specs", _kw("punch", "tata"), 1),
        ("How much is Tata Tiago EV?", _kw("tiago", "price"), 1),
        ("What is the range of MG Comet EV?", _kw("comet", "mg", "range"), 1),
        ("Mercedes EQS price in India", _kw("mercedes", "eqs", "price"), 1),
        ("BYD Seal top speed", _kw("byd", "seal", "top speed"), 1),
        ("Ola S1 X battery", _kw("ola", "s1 x", "battery"), 1),
        ("Ather Rizta Z charging time", _kw("ather", "rizta", "charging"), 1),
        ("Tell me about Ather 450X", _kw("ather", "450x"), 1),
        ("What is Ola S1 Pro top speed?", _kw("ola", "s1 pro", "top speed"), 1),
        ("Need TVS iQube details", _kw("tvs", "iqube"), 1),
        ("Price of Bajaj Chetak please", _kw("bajaj", "chetak", "price"), 1),
        ("Hero Vida V1 range", _kw("hero", "vida", "range"), 1),
        ("MG ZS EV charging time", _kw("mg", "zs", "charging"), 1),
        ("Tata Nexon EV battery", _kw("nexon", "battery"), 1),
    ]
    for query, expected, sources in easy_queries:
        add("easy", "direct", query, expected, sources)

    # Mid: 25
    mid_queries = [
        ("Compare Ola S1 Pro vs Ather 450X", _kw("ola", "ather"), 2),
        ("Which has more range, TVS iQube or Bajaj Chetak?", _kw("tvs", "bajaj", "range"), 2),
        ("Difference between Tata Nexon EV and MG ZS EV", _kw("nexon", "zs"), 2),
        ("Compare Mahindra XUV400 and Tata Punch EV", _kw("mahindra", "punch"), 2),
        ("BYD Atto 3 vs Hyundai Ioniq 5", _kw("byd", "hyundai"), 2),
        ("Kia EV6 versus Mercedes EQS", _kw("kia", "mercedes"), 2),
        ("Compare BYD Seal and Tata Nexon EV", _kw("byd", "nexon"), 2),
        ("Ola S1 X or Hero Vida V1, which is cheaper?", _kw("ola", "vida"), 2),
        ("Ather Rizta Z vs TVS iQube comparison", _kw("ather", "tvs"), 2),
        ("Compare Tata Tiago EV against MG Comet EV", _kw("tiago", "comet"), 2),
        ("Between Ather 450X and Ola S1 Pro, what should I pick?", _kw("ather", "ola"), 2),
        ("If I compare Punch EV with Nexon EV, what stands out?", _kw("punch", "nexon"), 2),
        ("Show me a side-by-side for Ioniq 5 and EV6", _kw("ioniq", "ev6"), 2),
        ("Nexon EV vs XUV400 which one looks stronger on paper?", _kw("nexon", "xuv400"), 2),
        ("What changes if I choose MG ZS EV over BYD Atto 3?", _kw("mg", "byd"), 2),
        ("Could you compare Ather 450X with TVS iQube?", _kw("ather", "tvs"), 2),
        ("S1 Pro compared with S1 X", _kw("s1 pro", "s1 x"), 2),
        ("Bajaj Chetak versus Hero Vida V1", _kw("bajaj", "vida"), 2),
        ("Comet EV vs Tiago EV for city use", _kw("comet", "tiago"), 2),
        ("Is Atto 3 better than ZS EV?", _kw("atto", "zs"), 2),
        ("Punch EV or Tiago EV for budget buyers", _kw("punch", "tiago"), 2),
        ("Compare Mercedes EQS and Kia EV6", _kw("mercedes", "kia"), 2),
        ("Need a quick comparison of Ather Rizta Z and Ola S1 X", _kw("rizta", "s1 x"), 2),
        ("How does Hyundai Ioniq 5 compare with BYD Seal?", _kw("ioniq", "seal"), 2),
        ("Compare TVS iQube, Bajaj Chetak, and Ather 450X", _kw("tvs", "bajaj", "ather"), 2),
    ]
    for query, expected, sources in mid_queries:
        add("mid", "direct", query, expected, sources, mode="comparison")

    # Hard: 25
    hard_queries = [
        ("Best electric scooter under 1.5 lakh", _kw("₹", "km"), 1),
        ("Long range electric bike under 2 lakh", _kw("range", "bike"), 1),
        ("Cheapest EV with fast charging", _kw("price", "charging"), 1),
        ("Recommend a family EV under 20 lakh", _kw("ev", "price"), 1),
        ("Which EV should I buy for a 70 km daily commute?", _kw("range", "km"), 1),
        ("Suggest an EV with at least 400 km range", _kw("400", "range"), 1),
        ("Need a premium electric car above 40 lakh", _kw("price", "car"), 1),
        ("Best scooter for college commute", _kw("scooter", "range"), 1),
        ("Give me a budget EV for city use", _kw("price", "range"), 1),
        ("Need a highway-friendly EV car", _kw("range", "car"), 1),
        ("Electric vehicle for family of five under 15 lakh", _kw("family", "price"), 1),
        ("I want the longest range EV you have", _kw("range"), 1),
        ("Suggest a reliable EV under 10 lakh", _kw("price", "ev"), 1),
        ("What electric scooter should I get if I want easy charging?", _kw("scooter", "charging"), 1),
        ("Find me a fast charging electric car", _kw("charging", "car"), 1),
        ("Any EV around 12 lakh with good range?", _kw("range", "price"), 1),
        ("Recommend an EV for daily office commute", _kw("range", "price"), 1),
        ("Need an EV with strong battery and decent range", _kw("battery", "range"), 1),
        ("Show budget-friendly scooters with decent range", _kw("scooter", "range"), 1),
        ("Can you suggest a practical electric hatchback?", _kw("ev", "price"), 1),
        ("What should I buy if I mostly drive in traffic?", _kw("city", "range"), 1),
        ("Recommend an electric car with low running stress", _kw("car", "range"), 1),
        ("Give me a good EV if charging access is limited", _kw("charging", "range"), 1),
        ("Best value electric car under 25 lakh", _kw("price", "car"), 1),
        ("I need an EV with solid daily usability, not just specs", _kw("range", "price"), 1),
    ]
    for query, expected, sources in hard_queries:
        add("hard", "vague", query, expected, sources)

    # Expert: 25
    expert_queries = [
        ("What is regenerative braking?", _kw("energy", "battery", "braking"), 0),
        ("Difference between AC charging and DC fast charging", _kw("ac", "dc", "charging"), 0),
        ("LFP vs NMC battery which is safer?", _kw("lfp", "nmc", "safer"), 0),
        ("Does fast charging degrade battery life?", _kw("fast charging", "degradation", "heat"), 0),
        ("Explain cell balancing in an EV battery management system", _kw("cell balancing", "battery", "health"), 0),
        ("EV vs petrol running cost over time", _kw("cost", "electricity", "petrol"), 0),
        ("Is it safe to charge an EV in heavy rain?", _kw("safe", "rain", "sealed"), 0),
        ("PM E-Drive vs FAME II", _kw("pm e-drive", "fame"), 0),
        ("Are solid state batteries available in Indian EVs yet?", _kw("solid-state", "lfp", "nmc"), 0),
        ("How does temperature affect EV range?", _kw("temperature", "range"), 0),
        ("What is CCS2 connector?", _kw("ccs2", "connector", "dc"), 0),
        ("What happens to old EV batteries after degradation?", _kw("second-life", "recycling"), 0),
        ("Can I install a 7kW charger in an apartment parking lot?", _kw("7 kw", "apartment", "load"), 0),
        ("Explain V2L technology", _kw("v2l", "vehicle-to-load"), 0),
        ("Explain V2V charging", _kw("vehicle-to-vehicle", "charging"), 0),
        ("who is the president of India?", _kw("ev", "electric"), 0),
        ("write me a python sorting script", _kw("ev", "electric"), 0),
        ("Is Tesla Model Y in this dataset?", _kw("dataset", "current"), 0),
        ("whiich is moar range ola s11 or aher?", _kw("ola", "ather", "range"), 1),
        ("best ev", _kw("budget", "range", "vehicle"), 0),
        ("which one should i buy?", _kw("budget", "range", "vehicle"), 0),
        ("give me specs", _kw("vehicle", "name"), 0),
        ("Tell me about Elon Musk and Tata Motors", _kw("ev", "electric"), 0),
        ("Can you compare a petrol car for me?", _kw("ev", "electric"), 0),
        ("What is its top speed?", _kw("vehicle", "name"), 0),
    ]
    for query, expected, sources in expert_queries:
        mode = "offtopic" if any(token in query.lower() for token in ["president", "python", "elon", "petrol"]) else "keywords"
        if "Tesla Model Y" in query:
            mode = "no_match"
        add("expert", "indirect", query, expected, sources, mode=mode)

    assert len(cases) == 100, len(cases)
    return cases


def score_case(case, answer, sources):
    answer_lower = (answer or "").lower()
    keywords = case["expected_keywords"]
    hits = sum(1 for keyword in keywords if keyword in answer_lower)

    if len(answer_lower.strip()) < 12:
        return False, hits

    mode = case["mode"]
    if mode == "offtopic":
        return (("ev" in answer_lower) or ("electric" in answer_lower)), hits
    if mode == "no_match":
        return any(token in answer_lower for token in ["dataset", "not available", "could not find", "current dataset"]), hits
    if mode == "comparison":
        both_present = hits >= max(2, math.ceil(len(keywords) * 0.5))
        comparison_shape = "|" in answer or "compare" in answer_lower or "difference" in answer_lower
        enough_sources = len(sources) >= case["expect_sources_min"]
        return (both_present and (comparison_shape or enough_sources)), hits

    enough_keywords = True
    if keywords:
        enough_keywords = hits >= max(1, math.ceil(len(keywords) * 0.4))
    enough_sources = len(sources) >= case["expect_sources_min"]
    return (enough_keywords and (enough_sources or case["expect_sources_min"] == 0)), hits


def run_benchmark():
    cases = build_cases()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "total_cases": len(cases),
        "passed": 0,
        "failed": 0,
        "avg_latency_ms": 0.0,
        "by_difficulty": defaultdict(lambda: {"total": 0, "passed": 0, "avg_latency_ms": 0.0}),
        "by_style": defaultdict(lambda: {"total": 0, "passed": 0, "avg_latency_ms": 0.0}),
        "samples": [],
    }
    results = []
    session_id = None
    latency_sum = 0.0

    for case in cases:
        start = time.perf_counter()
        response = requests.post(
            API_URL,
            json={"message": case["query"], **({"session_id": session_id} if session_id else {})},
            timeout=60,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        latency_sum += elapsed_ms

        payload = response.json()
        if not session_id and payload.get("session_id"):
            session_id = payload["session_id"]
        answer = payload.get("answer", "")
        sources = payload.get("sources", [])
        passed, hits = score_case(case, answer, sources)

        result = {
            **case,
            "http_status": response.status_code,
            "passed": passed,
            "keyword_hits": hits,
            "latency_ms": round(elapsed_ms, 2),
            "source_count": len(sources),
            "answer_preview": answer.replace("\n", " ")[:220],
        }
        results.append(result)

        bucket = summary["by_difficulty"][case["difficulty"]]
        bucket["total"] += 1
        bucket["passed"] += int(passed)
        bucket["avg_latency_ms"] += elapsed_ms

        style_bucket = summary["by_style"][case["style"]]
        style_bucket["total"] += 1
        style_bucket["passed"] += int(passed)
        style_bucket["avg_latency_ms"] += elapsed_ms

        if len(summary["samples"]) < 8:
            summary["samples"].append({
                "query": case["query"],
                "passed": passed,
                "latency_ms": round(elapsed_ms, 2),
                "answer_preview": result["answer_preview"],
            })

    summary["passed"] = sum(1 for item in results if item["passed"])
    summary["failed"] = len(results) - summary["passed"]
    summary["accuracy_percent"] = round((summary["passed"] / len(results)) * 100, 2)
    summary["avg_latency_ms"] = round(latency_sum / len(results), 2)

    for bucket in summary["by_difficulty"].values():
        bucket["accuracy_percent"] = round((bucket["passed"] / bucket["total"]) * 100, 2) if bucket["total"] else 0.0
        bucket["avg_latency_ms"] = round(bucket["avg_latency_ms"] / bucket["total"], 2) if bucket["total"] else 0.0
    for bucket in summary["by_style"].values():
        bucket["accuracy_percent"] = round((bucket["passed"] / bucket["total"]) * 100, 2) if bucket["total"] else 0.0
        bucket["avg_latency_ms"] = round(bucket["avg_latency_ms"] / bucket["total"], 2) if bucket["total"] else 0.0

    timestamp = int(time.time())
    json_path = REPORT_DIR / f"benchmark_chatbot_100_{timestamp}.json"
    md_path = REPORT_DIR / f"benchmark_chatbot_100_{timestamp}.md"

    json_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")

    lines = [
        "# EV Chatbot 100-Question Benchmark",
        "",
        f"- Accuracy: {summary['accuracy_percent']}%",
        f"- Passed: {summary['passed']}/{summary['total_cases']}",
        f"- Average latency: {summary['avg_latency_ms']} ms",
        "",
        "## By Difficulty",
    ]
    for difficulty, bucket in summary["by_difficulty"].items():
        lines.append(f"- {difficulty.title()}: {bucket['passed']}/{bucket['total']} ({bucket['accuracy_percent']}%), avg {bucket['avg_latency_ms']} ms")
    lines.append("")
    lines.append("## By Style")
    for style, bucket in summary["by_style"].items():
        lines.append(f"- {style.title()}: {bucket['passed']}/{bucket['total']} ({bucket['accuracy_percent']}%), avg {bucket['avg_latency_ms']} ms")
    lines.append("")
    lines.append("## Sample Results")
    for sample in summary["samples"]:
        lines.append(f"- `{sample['query']}` -> {'PASS' if sample['passed'] else 'FAIL'} in {sample['latency_ms']} ms")
        lines.append(f"  {sample['answer_preview']}")
    lines.append("")
    lines.append("## Failed Cases")
    for item in results:
        if not item["passed"]:
            lines.append(f"- [{item['difficulty']}/{item['style']}] `{item['query']}` -> {item['answer_preview']}")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"summary": summary, "json_report": str(json_path), "md_report": str(md_path)}, indent=2))


if __name__ == "__main__":
    run_benchmark()
