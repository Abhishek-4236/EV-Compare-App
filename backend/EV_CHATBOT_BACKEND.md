# EV Chatbot Backend

This backend implements an EV RAG pipeline with:

- Excel ingestion into structured JSON
- OpenAI embeddings for vehicle records
- FAISS vector index for semantic retrieval
- LLM query parsing for intent and filters
- Hybrid retrieval with vector search + structured filters
- FastAPI `/api/chat` endpoint with session history

## Architecture

1. `services/ev_catalog.py`
   Converts Excel rows into normalized `VehicleDocument` records and saves them as JSON.
2. `scripts/build_ev_knowledge_base.py`
   Reads the Excel file, creates embeddings with OpenAI, and saves a FAISS index.
3. `services/query_parser.py`
   Uses an OpenAI model to parse user intent and structured constraints.
4. `services/ev_rag.py`
   Performs filtered retrieval, fallback matching, and final answer generation.
5. `routers/chat.py`
   Exposes `/api/chat` and `/api/chat/stream`.

## Example queries

- `best EV under 15 lakh`
- `long range electric bike`
- `cheapest EV with fast charging`
- `compare Ola S1 Pro vs Ather 450X`

## Example `/api/chat` response

```json
{
  "success": true,
  "session_id": "a4de76f1-b9e6-4ad4-a4a4-3f1f3ea5f8ba",
  "answer": "For a budget under Rs. 15 lakh, the strongest options in the current dataset are ...",
  "intent": "recommendation",
  "parsed_query": {
    "intent": "recommendation",
    "rewritten_query": "best electric vehicle under 1500000 INR",
    "filters": {
      "min_price_inr": null,
      "max_price_inr": 1500000,
      "min_range_km": null,
      "vehicle_type": null,
      "brand": null,
      "charging_type": null,
      "fast_charging": null
    },
    "vehicle_names": [],
    "sort_by": "price",
    "user_goal": "best EV under 15 lakh"
  },
  "sources": [
    {
      "vehicle_id": "tata-nexon-ev-12",
      "name": "Tata Nexon EV",
      "price": 1450000,
      "range_km": 325
    }
  ]
}
```

## Run locally

1. Install Python dependencies:

```bash
pip install -r backend/requirements.txt
```

2. Configure environment variables in `backend/.env` or from `.env.example`:

- `OPENAI_API_KEY`
- `DATABASE_URL`

3. Build the EV knowledge base:

```bash
cd backend
python scripts/build_ev_knowledge_base.py
```

4. Start the API:

```bash
uvicorn main:app --reload
```

5. Send a test request:

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"best EV under 15 lakh\"}"
```

## Notes

- If the OpenAI parser fails, the backend falls back to a heuristic parser.
- If the LLM answer generation fails, the backend falls back to deterministic grounded summaries.
- If no exact match is found, the assistant suggests relaxed filters instead of returning an empty response.
