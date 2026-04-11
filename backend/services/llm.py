# backend/services/llm.py
import os
from groq import Groq
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from models import Vehicle, KnowledgeArticle
from .chat_analysis import is_compare_query, needs_explicit_vehicle

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")
HF_PROVIDER = os.getenv("HF_PROVIDER", "auto")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"

client = InferenceClient(token=HF_TOKEN, provider=HF_PROVIDER)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def format_price(p: int | None) -> str:
    if p is None: return "N/A"
    if p >= 10000000: return f"\u20b9{p / 10000000:.2f}Cr"
    if p >= 100000: return f"\u20b9{p / 100000:.1f}L"
    return f"\u20b9{p / 1000:.0f}K"

def build_specs(v: Vehicle) -> str:
    parts = [
        f"Price: {format_price(v.approx_price_inr)}",
        f"Range: {v.range_km} km" if v.range_km else None,
        f"Battery: {v.battery_kwh} kWh" if v.battery_kwh else None,
        f"Top speed: {v.top_speed_kmh} kmph" if v.top_speed_kmh else None,
        f"Charging: {v.charging_type}" if v.charging_type else None,
        f"FAME II: {format_price(v.fame2_subsidy_inr)}" if v.fame2_subsidy_inr else None,
        f"Rating: {v.overall_rating}/5" if v.overall_rating else None,
    ]
    return "; ".join([p for p in parts if p])

def fallback_answer(query: str, vehicles: list[Vehicle], articles: list[KnowledgeArticle] = None) -> str:
    ans_parts = []
    
    if articles:
        ans_parts.append("**EV Knowledge Article:**\n")
        for art in articles[:1]:
            # Provide a longer, more detailed snippet if it's the only article
            ans_parts.append(f"### {art.title}\n{art.content[:600]}...")
        ans_parts.append("\n\n*Source: EViq Technical Documents*")
        
        # If the query is purely knowledge (no vehicle intent), return now
        if not (is_compare_query(query) or needs_explicit_vehicle(query) or any(x in query.lower() for x in ["best", "recommend", "under", "budget"])):
            return "\n".join(ans_parts)
        
        ans_parts.append("\n---\n")

    if not vehicles:
        ans_parts.append("I could not find matching EVs. Please share a specific model or segment.")
        return "\n".join(ans_parts)

    if is_compare_query(query):
        if len(vehicles) < 2:
            return "Please provide two EV model names to compare."
        rows = vehicles[:3]
        table = [
            "| Vehicle | Price | Range | Battery | Top Speed |",
            "|---|---:|---:|---:|---:|",
        ]
        for v in rows:
            table.append(
                f"| {v.brand} {v.model} | {format_price(v.approx_price_inr)} | "
                f"{(v.range_km or 0)} km | {(v.battery_kwh or 0)} kWh | {(v.top_speed_kmh or 0)} kmph |"
            )
        ans_parts.append("Here is a side-by-side comparison:\n\n" + "\n".join(table))
        return "\n".join(ans_parts)

    if needs_explicit_vehicle(query):
        v = vehicles[0]
        ans_parts.append(f"{v.brand} {v.model} key specs: {build_specs(v)}")
        return "\n".join(ans_parts)

    q = query.lower()
    if any(x in q for x in ["cheapest", "lowest price", "budget"]):
        v = sorted(vehicles, key=lambda x: x.approx_price_inr or 10**9)[0]
        ans_parts.append(f"Best budget option from current matches is {v.brand} {v.model} at {format_price(v.approx_price_inr)}.")
        return "\n".join(ans_parts)

    if any(x in q for x in ["longest range", "best range", "maximum range", "top range"]):
        v = sorted(vehicles, key=lambda x: x.range_km or 0, reverse=True)[0]
        ans_parts.append(f"Top range option is {v.brand} {v.model} with about {v.range_km} km range.")
        return "\n".join(ans_parts)

    if any(x in q for x in ["subsidy", "fame"]):
        ranked = sorted(vehicles, key=lambda x: x.fame2_subsidy_inr or 0, reverse=True)[:3]
        lines = [f"{v.brand} {v.model}: Indicative central subsidy {format_price(int(v.fame2_subsidy_inr or 0))}" for v in ranked]
        ans_parts.append("Subsidy snapshot (verify latest state/dealer circular): " + "; ".join(lines))
        return "\n".join(ans_parts)

    lines = [f"{v.brand} {v.model} ({format_price(v.approx_price_inr)})" for v in vehicles[:5]]
    ans_parts.append("Here are the best matches: " + ", ".join(lines))
    return "\n".join(ans_parts)

def generate_answer(prompt: str, query: str, vehicles: list[Vehicle], articles: list[KnowledgeArticle] = None) -> str:
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=300,
            )
            ans = response.choices[0].message.content.strip()
            if ans: return ans
        except Exception: pass

    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
            model=HF_MODEL or "mistralai/Mistral-7B-Instruct-v0.2",
        )
        ans = response.choices[0].message.content.strip()
        if ans: return ans
    except Exception: pass

    return fallback_answer(query, vehicles, articles)
