"""
EViq Chat System - 40 Query Test Suite
Run this after starting the backend: python -m uvicorn main:app
Results are printed as a structured report.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8005/api/chat/"

QUERIES = [
    # === CATEGORY 1: Greetings (Expected: intent=greeting) ===
    {"q": "hie", "cat": "Greeting", "expect": "greeting response"},
    {"q": "hello", "cat": "Greeting", "expect": "greeting response"},
    {"q": "good morning", "cat": "Greeting", "expect": "greeting response"},
    {"q": "namaste", "cat": "Greeting", "expect": "greeting response"},

    # === CATEGORY 2: Off-topic (Expected: EV-only response) ===
    {"q": "who is the president of India?", "cat": "Off-topic", "expect": "redirect to EV topics"},
    {"q": "what is 2+2?", "cat": "Off-topic", "expect": "redirect to EV topics"},
    {"q": "write me a Python code", "cat": "Off-topic", "expect": "redirect to EV topics"},

    # === CATEGORY 3: Budget Recommendations (Novice) ===
    {"q": "best electric scooter under 1 lakh", "cat": "Budget Recommend", "expect": "scooter recommendations with prices"},
    {"q": "cheapest ev car in india", "cat": "Budget Recommend", "expect": "cheapest car EV listed"},
    {"q": "good family ev under 20 lakhs", "cat": "Budget Recommend", "expect": "4W family EVs under 20L"},
    {"q": "best bike for college student under 80000", "cat": "Budget Recommend", "expect": "budget 2W recommendations"},

    # === CATEGORY 4: Inventory (Expected: full list) ===
    {"q": "list all evs", "cat": "Inventory", "expect": "inventory summary with counts"},
    {"q": "show all vehicles", "cat": "Inventory", "expect": "inventory summary"},

    # === CATEGORY 5: Specific Vehicle Specs (Enthusiast) ===
    {"q": "what is the battery capacity of Ather 450X?", "cat": "Spec Lookup", "expect": "Ather 450X battery kWh"},
    {"q": "Ola S1 Pro range and top speed", "cat": "Spec Lookup", "expect": "Ola S1 Pro range + speed"},
    {"q": "Tata Nexon EV charging time", "cat": "Spec Lookup", "expect": "Nexon EV AC/DC charging time"},
    {"q": "MG ZS EV price and warranty", "cat": "Spec Lookup", "expect": "MG ZS EV price and warranty details"},

    # === CATEGORY 6: Comparisons — Vehicle vs Vehicle ===
    {"q": "compare Ather 450X vs Ola S1 Pro", "cat": "Vehicle Compare", "expect": "markdown table with specs side by side"},
    {"q": "Tata Nexon EV vs MG ZS EV which is better?", "cat": "Vehicle Compare", "expect": "comparison table"},
    {"q": "difference between Ola S1 Air and Ola S1 Pro", "cat": "Vehicle Compare", "expect": "comparison of both models"},

    # === CATEGORY 7: Concept Comparisons ===
    {"q": "AC charging vs DC charging which is better?", "cat": "Concept Compare", "expect": "explanation of AC vs DC charging"},
    {"q": "LFP vs NMC battery which is safer for Indian weather?", "cat": "Concept Compare", "expect": "LFP vs NMC comparison"},
    {"q": "EV vs petrol running cost in India", "cat": "Concept Compare", "expect": "cost comparison EV vs petrol"},

    # === CATEGORY 8: Knowledge / General EV ===
    {"q": "what is regenerative braking?", "cat": "Knowledge", "expect": "explanation of regen braking"},
    {"q": "how does cell balancing work in BMS?", "cat": "Knowledge", "expect": "BMS cell balancing explanation"},
    {"q": "does fast charging damage battery life?", "cat": "Knowledge", "expect": "honest answer on fast charge impact"},
    {"q": "can EVs work in rain?", "cat": "Knowledge", "expect": "IP rating and water resistance info"},
    {"q": "what is the difference between FAME II and PM E-Drive?", "cat": "Knowledge", "expect": "policy comparison"},

    # === CATEGORY 9: Subsidies ===
    {"q": "what is FAME II subsidy for electric scooters?", "cat": "Subsidy", "expect": "FAME II subsidy amount for 2W"},
    {"q": "which EVs get the most government subsidy?", "cat": "Subsidy", "expect": "ranked list of subsidized EVs"},
    {"q": "Maharashtra EV subsidy amount", "cat": "Subsidy", "expect": "state subsidy info or redirect"},

    # === CATEGORY 10: Charging Stations / Location ===
    {"q": "charging stations near Bengaluru", "cat": "Location", "expect": "station query redirect or data"},
    {"q": "fast charging points in Delhi", "cat": "Location", "expect": "location-based response"},

    # === CATEGORY 11: Pronoun / Context Follow-up ===
    {"q": "what is its battery capacity?", "cat": "Pronoun Follow-up", "expect": "uses last vehicle from session OR asks for clarification"},

    # === CATEGORY 12: Expert Technical Queries ===
    {"q": "explain the C-rating of NMC battery cells in EVs", "cat": "Expert Technical", "expect": "technical explanation with NMC/C-rate context"},
    {"q": "what is the PMSM vs BLDC motor efficiency difference in Indian EV scooters?", "cat": "Expert Technical", "expect": "technical motor comparison"},
    {"q": "how does thermal management affect battery lifecycle in tropical climates?", "cat": "Expert Technical", "expect": "detailed technical answer on thermal management"},
    {"q": "what is the real-world energy density trade-off between LFP and NMC cells at 40 degrees Celsius?", "cat": "Expert Technical", "expect": "expert-level battery chemistry answer"},

    # === CATEGORY 13: Edge / Ambiguous ===
    {"q": "best ev", "cat": "Ambiguous", "expect": "asks for segment/budget OR gives top-rated"},
    {"q": "which one should I buy?", "cat": "Ambiguous", "expect": "clarification requested"},
    {"q": "give me specs", "cat": "Ambiguous", "expect": "asks for specific model name"},
]

def run_tests():
    results = []
    session_id = None

    print(f"\n{'='*70}")
    print(f"  EViq Chat System — 40 Query Test Report")
    print(f"{'='*70}\n")

    for i, item in enumerate(QUERIES, 1):
        time.sleep(0.4)  # be gentle on the API
        try:
            payload = {"message": item["q"]}
            if session_id:
                payload["session_id"] = session_id

            resp = requests.post(BASE_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if not session_id and data.get("session_id"):
                session_id = data["session_id"]

            answer = data.get("answer", "")
            sources = data.get("sources", [])
            short = answer[:120].replace("\n", " ") + ("..." if len(answer) > 120 else "")

            status = "✅ OK" if answer and len(answer) > 10 else "⚠️  SHORT"
            results.append({"n": i, "cat": item["cat"], "q": item["q"], "status": status, "sources": len(sources), "answer": short})

            print(f"[{i:02d}] {status}  [{item['cat']}]")
            print(f"      Q: {item['q']}")
            print(f"      A: {short}")
            if sources:
                print(f"      🔗 Sources: {len(sources)} vehicle(s)")
            print()

        except Exception as e:
            print(f"[{i:02d}] ❌ ERROR  [{item['cat']}]")
            print(f"      Q: {item['q']}")
            print(f"      Error: {e}\n")
            results.append({"n": i, "cat": item["cat"], "q": item["q"], "status": "❌ ERROR", "sources": 0, "answer": str(e)})

    # Summary
    ok = sum(1 for r in results if "✅" in r["status"])
    warn = sum(1 for r in results if "⚠️" in r["status"])
    err = sum(1 for r in results if "❌" in r["status"])

    print(f"\n{'='*70}")
    print(f"  SUMMARY: {len(QUERIES)} queries run")
    print(f"  ✅ OK: {ok}  |  ⚠️  Short/Weak: {warn}  |  ❌ Error: {err}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_tests()
