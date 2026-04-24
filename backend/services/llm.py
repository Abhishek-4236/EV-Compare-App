import logging
import re

from google import genai
from google.genai import types
from core.config import settings

from models import KnowledgeArticle, Vehicle
from .chat_analysis import QueryPlan

logger = logging.getLogger(__name__)

GEMINI_API_KEY = settings.GEMINI_API_KEY

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=8),
    )
else:
    client = None

def format_price(price: int | float | None) -> str:
    if not price:
        return "N/A"
    if price >= 10000000:
        return f"₹{price / 10000000:.2f}Cr"
    if price >= 100000:
        return f"₹{price / 100000:.1f}L"
    return f"₹{price / 1000:.0f}K"

def build_specs(vehicle: Vehicle) -> str:
    parts = [
        f"Price: {format_price(vehicle.approx_price_inr)}",
        f"Range: {vehicle.range_km} km" if vehicle.range_km else None,
        f"Battery: {vehicle.battery_kwh} kWh" if vehicle.battery_kwh else None,
        f"Top speed: {vehicle.top_speed_kmh} kmph" if vehicle.top_speed_kmh else None,
        f"Charging: {vehicle.charging_type}" if vehicle.charging_type else None,
    ]
    if vehicle.extra_info:
        for k, v in vehicle.extra_info.items():
            parts.append(f"{k}: {v}")
    return "; ".join([part for part in parts if part])

def _article_reference(articles: list[KnowledgeArticle] | None) -> str:
    if not articles:
        return ""
    article = articles[0]
    snippet = re.sub(r"\s+", " ", (article.content or "")).strip()
    snippet = snippet[:220].rstrip(" .,;:")
    if snippet:
        return f"\n\nWhy/Reference: {article.title}. {snippet}..."
    return f"\n\nWhy/Reference: {article.title}."

def _general_knowledge_answer(query: str, articles: list[KnowledgeArticle] | None) -> str:
    label = "General EV knowledge answer, not model-specific dataset data."
    q = (query or "").lower()

    if "regen" in q or "regenerative braking" in q:
        return f"{label} Regenerative braking lets an EV recover some energy during deceleration and feed it back into the battery. It helps improve efficiency, reduces brake wear, and is most useful in city traffic with frequent slowing."
    if {"ac", "dc"}.issubset(set(re.findall(r"[a-z0-9]+", q))) and ("charging" in q or "batter" in q):
        return f"{label} AC charging sends alternating current to the car, and the onboard charger converts it to DC for the battery. DC fast charging converts power outside the vehicle and sends DC directly to the battery, so it charges much faster but usually costs more and creates more heat."
    if "lfp" in q and "nmc" in q:
        return f"{label} LFP batteries are usually safer, more thermally stable, and better for hot conditions and frequent charging. NMC batteries usually offer better energy density and stronger range for the same battery size, but need tighter thermal management."
    if "fast charging" in q and "battery life" in q:
        return f"{label} Frequent fast charging can increase battery heat and slightly accelerate degradation over time, especially in hot weather. It is usually fine for occasional highway use, while slow or overnight charging is gentler for daily charging."
    if "cell balancing" in q or "bms" in q:
        return f"{label} Cell balancing is a battery-management-system function that keeps battery cells at similar voltage levels. That improves safety, usable capacity, and long-term battery health because one weak or overcharged cell can limit the whole pack."
    if "petrol" in q and "ev" in q and "running cost" in q:
        return f"{label} EVs usually have much lower per-kilometer running cost than petrol vehicles because electricity is cheaper than fuel and EV maintenance is simpler. The exact savings depend on tariff, efficiency, annual kilometers, and whether you mostly charge at home or rely on public fast charging."
    if "fire" in q and "rain" in q:
        return f"{label} A healthy EV battery should not catch fire just because of rain. Modern EV packs are sealed and designed for water exposure, but flood damage, poor-quality aftermarket work, or a battery fault can still create risk and should be inspected."
    if "pm e-drive" in q and "fame" in q:
        return f"{label} PM E-Drive is not exactly the same program as FAME II. They are related central EV support schemes, but they can differ in period, scope, and incentive structure, so policy details should be verified from the latest government notification."

    if articles:
        article = articles[0]
        cleaned = re.sub(r"\s+", " ", article.content or "").strip()
        if cleaned:
            summary = cleaned[:320].rstrip(" .,;:")
            return f"{label} {summary}...{_article_reference(articles)}"
    return f"{label} I do not have a strong supporting article match, so please verify the latest manufacturer or policy source for this topic."

def fallback_answer(query: str, vehicles: list[Vehicle], articles: list[KnowledgeArticle] | None = None, plan: QueryPlan | None = None) -> str:
    plan_intent = plan.intent if plan else None
    q = (query or "").lower().strip()
    q = re.sub(r'[?.,!:]', '', q)

    if plan_intent == "inventory":
        return "I can summarize the EV inventory, but that response should come from the inventory handler."

    if plan_intent in {"knowledge", "concept_compare"}:
        return _general_knowledge_answer(query, articles)

    if not vehicles:
        if plan_intent == "spec":
            return "That specific data is not available in my current dataset."
        if plan_intent == "vehicle_compare":
            return "That specific comparison is not available in my current dataset. Please share two model names that exist in the current EV database."
        return "I could not find matching EVs in the current dataset. Please share a specific model, segment, or budget."

    if plan_intent == "vehicle_compare":
        rows = vehicles[:3]
        lead = ""
        if "range" in q:
            best = max(rows, key=lambda item: item.range_km or 0)
            lead = f"{best.brand} {best.model} has the highest listed range in the current dataset at about {best.range_km} km.\n\n"
        elif "charging" in q:
            charging_types = {f"{vehicle.brand} {vehicle.model}: {vehicle.charging_type or 'N/A'}" for vehicle in rows}
            if len({vehicle.charging_type for vehicle in rows}) == 1:
                lead = "Both models show the same charging type in the current dataset, so I cannot claim one is better on DC fast charging from the available data.\n\n"
            lead += "Charging snapshot: " + "; ".join(sorted(charging_types)) + "\n\n"
        
        table = [
            f"{lead}Here is a side-by-side comparison:",
            "",
            "| Vehicle | Price | Range | Battery | Top Speed |",
            "|---|---:|---:|---:|---:|",
        ]
        for vehicle in rows:
            table.append(
                f"| {vehicle.brand} {vehicle.model} | {format_price(vehicle.approx_price_inr)} | "
                f"{vehicle.range_km or 0} km | {vehicle.battery_kwh or 0} kWh | {vehicle.top_speed_kmh or 0} kmph |"
            )
        return "\n".join(table)

    if plan_intent == "spec":
        vehicle = vehicles[0]
        return f"{vehicle.brand} {vehicle.model} key specs: {build_specs(vehicle)}"

    if any(token in q for token in ["cheapest", "lowest price", "budget"]):
        vehicle = sorted(vehicles, key=lambda item: item.approx_price_inr or 10**9)[0]
        return f"Best budget option from current matches is {vehicle.brand} {vehicle.model} at {format_price(vehicle.approx_price_inr)}."

    if any(token in q for token in ["longest range", "best range", "maximum range", "top range"]):
        vehicle = sorted(vehicles, key=lambda item: item.range_km or 0, reverse=True)[0]
        return f"Top range option is {vehicle.brand} {vehicle.model} with about {vehicle.range_km} km range."

    if plan_intent == "subsidy" or any(token in q for token in ["subsidy", "fame", "pm e-drive"]):
        ranked = sorted(vehicles, key=lambda item: item.approx_price_inr or 0, reverse=True)[:3]
        lines = [f"{vehicle.brand} {vehicle.model}" for vehicle in ranked]
        return "Subsidy snapshot from the current dataset (verify latest policy circular): " + "; ".join(lines)

    if plan_intent == "recommend":
        lines = [f"{vehicle.brand} {vehicle.model} ({format_price(vehicle.approx_price_inr)})" for vehicle in vehicles[:5]]
        return "Here are the best matches from the current dataset: " + ", ".join(lines)

    lines = [f"{vehicle.brand} {vehicle.model} ({format_price(vehicle.approx_price_inr)})" for vehicle in vehicles[:5]]
    return "Here are relevant EVs from the current dataset: " + ", ".join(lines)

def generate_answer(prompt: str, query: str, vehicles: list[Vehicle], articles: list[KnowledgeArticle] | None = None, plan: QueryPlan | None = None) -> str:
    if client:
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are an Indian EV expert. Reply in a natural chat style, answer the user's actual intent first, use only the provided context for model-specific claims, and if data is missing say you do not know.",
                    temperature=0.4,
                    max_output_tokens=320,
                ),
            )
            answer = response.text.strip()
            if answer:
                return answer
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            print(f"Gemini generation failed: {e}")

    # Fallback to pure offline DB answers if API fails or key is missing
    return fallback_answer(query, vehicles, articles, plan)
