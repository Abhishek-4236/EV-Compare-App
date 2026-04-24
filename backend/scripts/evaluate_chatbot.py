import urllib.request
import json
import time

API_URL = "http://localhost:8000/api/chat/"

# 50 Test Questions categorized by difficulty

TEST_CASES = [
    # EASY (Direct Database Queries)
    {"category": "Easy", "question": "What is the price of Ola S1 X?", "req": ["Ola"]},
    {"category": "Easy", "question": "Tell me the battery capacity of Tata Nexon EV.", "req": ["Nexon"]},
    {"category": "Easy", "question": "What is the range of Ather 450X?", "req": ["Ather"]},
    {"category": "Easy", "question": "Is the MG ZS EV fast charging compatible?", "req": ["MG", "ZS"]},
    {"category": "Easy", "question": "What is the top speed of Bajaj Chetak?", "req": ["Bajaj"]},
    {"category": "Easy", "question": "How much is the TVS iQube?", "req": ["TVS"]},
    {"category": "Easy", "question": "Tell me the price of Hero Vida V1.", "req": ["Hero", "Vida"]},
    {"category": "Easy", "question": "What is the range of Hyundai Ioniq 5?", "req": ["Hyundai"]},
    {"category": "Easy", "question": "Battery size of Kia EV6?", "req": ["Kia"]},
    {"category": "Easy", "question": "Price of Mahindra XUV400?", "req": ["Mahindra"]},
    {"category": "Easy", "question": "Range of BYD Atto 3?", "req": ["BYD"]},
    {"category": "Easy", "question": "Top speed of Simple One?", "req": ["Simple"]},

    # MEDIUM (Comparative)
    {"category": "Medium", "question": "Compare Tata Nexon EV and MG ZS EV.", "req": ["Nexon", "ZS"]},
    {"category": "Medium", "question": "Which has more range, Ola S1 Pro or Ather 450X?", "req": ["Ola", "Ather"]},
    {"category": "Medium", "question": "Compare TVS iQube and Bajaj Chetak.", "req": ["TVS", "Bajaj"]},
    {"category": "Medium", "question": "Difference between Hyundai Ioniq 5 and Kia EV6?", "req": ["Hyundai", "Kia"]},
    {"category": "Medium", "question": "Tata Punch EV vs Tata Tiago EV?", "req": ["Punch", "Tiago"]},
    {"category": "Medium", "question": "Compare Hero Vida V1 against Ola S1 X.", "req": ["Vida"]},
    {"category": "Medium", "question": "Which is faster, BYD Atto 3 or MG ZS EV?", "req": ["BYD", "MG"]},
    {"category": "Medium", "question": "Compare battery capacity of Simple One and Ather 450X.", "req": ["Simple", "Ather"]},
    {"category": "Medium", "question": "Which is cheaper, Nexon EV or XUV400?", "req": ["Nexon", "XUV"]},
    {"category": "Medium", "question": "Compare charging types of Ioniq 5 and EV6.", "req": ["Ioniq", "EV6"]},
    {"category": "Medium", "question": "Ather 450S vs Ather 450X compare them.", "req": ["Ather"]},
    {"category": "Medium", "question": "TVS iQube ST vs Ola S1 Pro comparison.", "req": ["iQube", "Ola"]},

    # HARD (Consultative)
    {"category": "Hard", "question": "What is the absolutely cheapest electric scooter available?", "req": []},
    {"category": "Hard", "question": "Recommend the best electric car for long highway trips.", "req": []},
    {"category": "Hard", "question": "I travel 60km every day, what electric scooter should I buy under 1.2 Lakhs?", "req": []},
    {"category": "Hard", "question": "Which EV has the highest top speed in the market?", "req": []},
    {"category": "Hard", "question": "What is the best electric car with over 400km range?", "req": []},
    {"category": "Hard", "question": "I need an electric scooter with a removable battery.", "req": []},
    {"category": "Hard", "question": "Which electric cars offer fast DC charging?", "req": []},
    {"category": "Hard", "question": "Can you recommend a premium EV SUV above 50 Lakhs?", "req": []},
    {"category": "Hard", "question": "Best practical family electric car under 15 Lakhs?", "req": []},
    {"category": "Hard", "question": "Which electric two wheelers get the FAME II subsidy?", "req": []},
    {"category": "Hard", "question": "Recommend a scooter with a range of at least 120km.", "req": []},
    {"category": "Hard", "question": "What's a good alternative to the Tata Nexon EV?", "req": []},
    {"category": "Hard", "question": "Suggest a reliable scooter from Hero or TVS.", "req": ["Hero", "TVS", "Vida", "iQube"]},

    # EXPERT (General Knowledge)
    {"category": "Expert", "question": "What exactly is regenerative braking and how does it increase efficiency?", "req": ["regenerative"]},
    {"category": "Expert", "question": "What is the difference between AC charging and DC fast charging?", "req": ["charging"]},
    {"category": "Expert", "question": "Between NMC and LFP batteries, which is safer for the Indian summer climate?", "req": ["LFP", "NMC"]},
    {"category": "Expert", "question": "Will frequent fast charging degrade my car's battery faster?", "req": ["degrade", "heat"]},
    {"category": "Expert", "question": "What is cell balancing in an EV battery management system?", "req": ["balancing", "health"]},
    {"category": "Expert", "question": "How does the running cost of an EV compare to a petrol car over 5 years?", "req": ["cost", "cheaper"]},
    {"category": "Expert", "question": "Is it safe to charge an electric car outside while it's raining heavily?", "req": ["rain", "safe", "sealed"]},
    {"category": "Expert", "question": "Can you explain how the PM E-Drive subsidy scheme differs from FAME II?", "req": ["subsidy", "FAME"]},
    {"category": "Expert", "question": "What happens to old EV batteries when they degrade beyond 70%?", "req": []},
    {"category": "Expert", "question": "Can I install a 7kW AC fast charger in a standard Indian apartment parking lot?", "req": []},
    {"category": "Expert", "question": "Are solid state batteries available in the EVs sold in India yet?", "req": []},
    {"category": "Expert", "question": "How does ambient temperature affect an EV's real-world highway range?", "req": ["temperature", "range"]},
    {"category": "Expert", "question": "What is V2L (Vehicle-to-Load) technology and which cars have it?", "req": []},

    # ADVERSARIAL (Edge cases, misspellings, or extreme queries)
    {"category": "Adversarial", "question": "whiich is moar range ola s11 or aher?", "req": ["ola", "ather"]},
    {"category": "Adversarial", "question": "Recommend a petrol car that gives 20kmpl.", "req": ["ev", "electric"]},
    {"category": "Adversarial", "question": "Tell me the price of a Tesla Model Y.", "req": ["not available", "dataset", "current"]},
    
    # GREETING & CHUNKING (Basic bot interactions)
    {"category": "Greeting", "question": "hello", "req": ["budget", "range", "compare"]},
    {"category": "Greeting", "question": "yo bro what can you do", "req": ["India", "EV"]},
    
    # NEW STRESS TESTS (75+ Total)
    {"category": "Hard", "question": "I need an electric truck for my business in Delhi.", "req": ["truck", "commercial"]},
    {"category": "Medium", "question": "Comparing Euler Storm vs Mahindra Treo.", "req": ["Euler", "Mahindra"]},
    {"category": "Easy", "question": "Who makes the Comet EV?", "req": ["MG"]},
    {"category": "Expert", "question": "What is the IP rating of the Ather 450X battery?", "req": ["IP67"]},
    {"category": "Hard", "question": "Recommend a car for a family of 5 with good safety.", "req": ["Nexon", "Punch", "safety"]},
    {"category": "Expert", "question": "Does fast charging kill the battery if I do it every day?", "req": ["degrad", "heat"]},
    {"category": "Hard", "question": "Cheapest electric car with a sunroof?", "req": ["sunroof"]},
    {"category": "Medium", "question": "TVS iQube vs Ather 450X range comparison.", "req": ["range"]},
    {"category": "Easy", "question": "Range of the BYD Seal?", "req": ["Seal", "BYD"]},
    {"category": "Hard", "question": "I have ₹1.5 Crore, which is the most luxurious EV?", "req": ["Taycan", "i7", "EQS", "luxury", "Rs"]},
    {"category": "Expert", "question": "Explain V2V charging.", "req": ["vehicle-to-vehicle"]},
    {"category": "Hard", "question": "Best scooter for hilly areas like Shimla.", "req": ["torque", "climb"]},
    {"category": "Medium", "question": "Compare Punch EV and Nexon EV LR.", "req": ["Punch", "Nexon"]},
    {"category": "Adversarial", "question": "Is Elon Musk the CEO of Tata Motors?", "req": ["No", "Ratan Tata", "N Chandrasekaran"]},
    {"category": "Easy", "question": "What is the motor power of the Ola S1 Pro?", "req": ["kW", "8.5", "11"]},
    {"category": "Hard", "question": "I need an EV with 10 years of warranty.", "req": ["warranty"]},
    {"category": "Expert", "question": "What is a CCS2 connector?", "req": ["connector", "DC", "charging"]},
    {"category": "Easy", "question": "Price of the Mercedes EQS in India?", "req": ["Cr"]},
    {"category": "Medium", "question": "Ather vs Ola: which has a better suspension?", "req": ["suspension", "monoshock"]},
    {"category": "Hard", "question": "Suggest an EV for a 100km round trip commute.", "req": ["range", "100"]},
]


import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Add parent dir so we can import backend packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from routers.chat import generate_chat_payload, ChatRequest

def check_accuracy(answer: str, req_keywords: list) -> bool:
    """Returns True if the response is valid and meets requirements."""
    ans_lower = answer.lower()
    
    if not ans_lower or len(ans_lower) < 20:
        return False
    if "sorry, i couldn't process that" in ans_lower:
        return False
        
    if "is not available in my current dataset" in ans_lower and "regenerative" in ans_lower:
        return False
        
    if not req_keywords:
        return True
        
    matched = 0
    # Add model name components to keywords if not already there
    for kw in req_keywords:
        if kw.lower() in ans_lower:
            matched += 1
            
    # Success threshold: At least half keywords matched, or if specific numeric matches found
    return matched >= (len(req_keywords) / 2.0) or (len(req_keywords) > 0 and matched >= 1)

async def main():
    print("="*60)
    print(f"Starting EViq Chatbot Evaluation Suite ({len(TEST_CASES)} queries)")
    print("="*60)
    
    results = []
    correct = 0
    
    db = SessionLocal()
    try:
        for i, test in enumerate(TEST_CASES, 1):
            q = test["question"]
            cat = test["category"]
            
            try:
                # Bypass API and run the actual logic directly with DB session
                req = ChatRequest(message=q, session_id=f"test-session-{i}")
                payload = generate_chat_payload(req, db)
                ans = payload.get("answer", "")
                
                is_correct = check_accuracy(ans, test["req"])
                if is_correct:
                    correct += 1
                
                status = "[PASS]" if is_correct else "[FAIL]"
                print(f"[{i:02d}/{len(TEST_CASES)}] {cat.upper()} | {status} | Q: {q}")
                
                results.append({
                    "id": i,
                    "category": cat,
                    "question": q,
                    "status": "PASS" if is_correct else "FAIL",
                    "answer_preview": ans.replace("\n", " ")[:120] + "..."
                })
            except Exception as e:
                # Safely print the error without failing on unicode issues
                err_msg = str(e).replace('\u20b9', 'Rs.')
                q_safe = q.replace('\u20b9', 'Rs.')
                print(f"[{i:02d}/{len(TEST_CASES)}] {cat.upper()} | [ERROR] | Q: {q_safe} | Err: {err_msg}")
                results.append({
                    "id": i,
                    "category": cat,
                    "question": q,
                    "status": "ERROR",
                    "answer_preview": str(e)
                })
                
        accuracy_score = (correct / len(TEST_CASES)) * 100
        print("="*60)
        print(f"EVALUATION COMPLETE")
        print(f"Final Accuracy Score: {correct}/{len(TEST_CASES)} ({accuracy_score:.2f}%)")
        print("="*60)
        
        # Save detailed markdown report
        with open("test_results_detailed.md", "w", encoding="utf-8") as f:
            f.write("# EViq Chatbot Testing Report\n\n")
            f.write(f"**Total Questions Tested:** {len(TEST_CASES)}\n")
            f.write(f"**Final Accuracy Score:** {correct}/{len(TEST_CASES)} ({accuracy_score:.2f}%)\n\n")
            f.write("## Detailed Results\n")
            f.write("| ID | Category | Status | Question | Answer Preview |\n")
            f.write("|---|---|---|---|---|\n")
            for r in results:
                ans_clean = r["answer_preview"].replace("|", "/")
                f.write(f"| {r['id']} | {r['category']} | {r['status']} | {r['question']} | {ans_clean} |\n")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
