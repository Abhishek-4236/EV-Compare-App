import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from routers.chat import generate_chat_payload, ChatRequest

QUESTIONS = [
    # ---- EASY (25 Questions) - Mostly direct fact retrieval & simple questions ----
    ("Easy", "What is the price of Ola S1 X?"),
    ("Easy", "Tell me the battery capacity of Tata Nexon EV."),
    ("Easy", "How far can the Ather 450X go on a single charge?"),
    ("Easy", "Is the MG ZS EV fast charging compatible?"),
    ("Easy", "What is the top speed of Bajaj Chetak?"),
    ("Easy", "How much does the TVS iQube cost?"),
    ("Easy", "Tell me the price of Hero Vida V1."),
    ("Easy", "What is the range of Hyundai Ioniq 5?"),
    ("Easy", "Battery size of Kia EV6?"),
    ("Easy", "Price of Mahindra XUV400?"),
    ("Easy", "Range of BYD Atto 3?"),
    ("Easy", "Top speed of Simple One?"),
    ("Easy", "Does the Tata Tiago EV have a sunroof?"), # Indirect based on extra info
    ("Easy", "What kind of charging does the Volvo XC40 Recharge use?"),
    ("Easy", "Show me the tyre size of the Ola S1 Pro."),
    ("Easy", "How many kilometers does the MG Comet EV give?"),
    ("Easy", "Is the Tata Punch EV available to buy right now?"),
    ("Easy", "What's the wheel size on a Bajaj Chetak?"),
    ("Easy", "Tell me about the warranty on the Ather 450S."),
    ("Easy", "What category is the Euler Storm?"),
    ("Easy", "Is there a GPS on the TVS iQube ST?"),
    ("Easy", "Give me the battery info for the Hyundai Kona."),
    ("Easy", "How long does it take to charge a BYD Seal?"),
    ("Easy", "What is the safety rating for Tata Nexon EV?"),
    ("Easy", "Do you have data on the Ola S1 Air?"),

    # ---- MEDIUM (25 Questions) - Comparative and slightly indirect ----
    ("Medium", "Compare Tata Nexon EV and MG ZS EV."),
    ("Medium", "Which has more range, Ola S1 Pro or Ather 450X?"),
    ("Medium", "If I want to choose between TVS iQube and Bajaj Chetak, which is better?"),
    ("Medium", "Difference between Hyundai Ioniq 5 and Kia EV6?"),
    ("Medium", "Tata Punch EV vs Tata Tiago EV?"),
    ("Medium", "I'm looking at the Hero Vida V1 and Ola S1 X, compare them for me."),
    ("Medium", "Which accelerates faster, BYD Atto 3 or MG ZS EV?"),
    ("Medium", "Compare the battery capacity of Simple One and Ather 450X."),
    ("Medium", "Which will hurt my wallet less, Nexon EV or XUV400?"), # Indirect language for cheap
    ("Medium", "Compare charging types of Ioniq 5 and EV6."),
    ("Medium", "Ather 450S vs Ather 450X compare them."),
    ("Medium", "Put TVS iQube ST and Ola S1 Pro head to head."),
    ("Medium", "Which EV has a bigger battery: BYD Seal or Hyundai Ioniq 5?"),
    ("Medium", "Does the MG Comet or Tata Tiago EV take longer to charge?"),
    ("Medium", "Between the Altigreen NEEV and Mahindra Treo, what's different?"),
    ("Medium", "Comparing Euler Storm vs Mahindra Jayo - what are the specs?"),
    ("Medium", "Which two wheeler is cheaper, Bajaj Chetak or TVS iQube?"),
    ("Medium", "I want an SUV. How does the Nexon EV compare to the XUV400?"),
    ("Medium", "Which one has a longer warranty, MG ZS EV or Tata Nexon?"),
    ("Medium", "Do they both use AC charging? Nexon EV vs BYD Atto 3."),
    ("Medium", "Compare battery life on the Ola line vs Ather line."),
    ("Medium", "Which car gives more kms per charge between the Tiago EV and Comet EV?"),
    ("Medium", "I need to know the price difference between Ather 450S and 450X."),
    ("Medium", "Is the battery bigger in the Hyundai Kona or MG ZS?"),
    ("Medium", "Show me how the TVS X compares to the Simple One."),

    # ---- HARD (25 Questions) - Consultative, indirect human speech, filtering ----
    ("Hard", "My budget is super tight, what is the absolute cheapest electric scooter I can get?"),
    ("Hard", "Can you recommend the best electric car for long highway road trips?"),
    ("Hard", "I travel about 60km every single day for work, what electric scooter should I buy if I only have 1.2 Lakhs?"),
    ("Hard", "I have a need for speed, which EV has the highest top speed in the market right now?"),
    ("Hard", "I suffer from range anxiety. What is the best electric car with over 400km range?"),
    ("Hard", "I live in an apartment without a plug on the ground floor. I need an electric scooter with a removable battery."),
    ("Hard", "I'm always in a rush. Which electric cars offer really fast DC charging?"),
    ("Hard", "Money is no object, my budget is above 50 Lakhs. Recommend a premium EV SUV."), # Human-like indirect budget
    ("Hard", "I need a solid, practical family electric car under 15 Lakhs."),
    ("Hard", "Are there any electric two-wheelers that actually get the FAME II subsidy right now?"),
    ("Hard", "Recommend a scooter that won't die on me quickly, it needs a range of at least 120km."),
    ("Hard", "Everyone has a Tata Nexon EV. What's a good alternative to it?"),
    ("Hard", "Suggest a very reliable scooter specifically from either Hero or TVS."),
    ("Hard", "I need an electric truck for my transport business based in Delhi."),
    ("Hard", "Recommend a car for a family of 5 with really good safety ratings."),
    ("Hard", "Cheapest electric car that comes with a sunroof?"),
    ("Hard", "I have ₹1.5 Crore sitting around, which is the most luxurious EV I can get?"),
    ("Hard", "I live in a hilly area like Shimla, what scooter will actually climb the hills well?"),
    ("Hard", "I need an EV with an insane warranty, like 8 to 10 years."),
    ("Hard", "Suggest an EV that can comfortably do a 100km round trip commute every day without charging in between."),
    ("Hard", "Looking for a three wheeler for cargo delivery under 4 Lakhs."),
    ("Hard", "What's the best high-range scooter I can buy for 1.5 Lakhs?"),
    ("Hard", "I drive an Uber. Suggest an electric car with low running costs and good boot space."),
    ("Hard", "Give me a cheap electric bike, not a scooter, under 1.5L."),
    ("Hard", "Can you find me an EV from MG that is under 10 lakhs?"),

    # ---- EXPERT / OUT OF DATA / ADVERSARIAL (25 Questions) - Deep knowledge, curveballs ----
    ("Expert", "Hey bro, break down exactly what regenerative braking is and how it actually increases my efficiency?"),
    ("Expert", "Explain the technical difference between AC charging and DC fast charging in simple terms."),
    ("Expert", "Between NMC and LFP battery chemistries, which one is actually safer for the scorching Indian summer heat?"),
    ("Expert", "If I fast charge my car every single day, will it kill the battery faster?"),
    ("Expert", "What does cell balancing mean in the context of an EV battery management system (BMS)?"),
    ("Expert", "How drastically does the running cost of an EV compare to a typical petrol car over a 5-year ownership period?"),
    ("Expert", "Is it genuinely safe to charge my electric car outside when it's pouring rain and flooded?"),
    ("Expert", "Can you explain how the new PM E-Drive subsidy scheme differs technically from the old FAME II?"),
    ("Expert", "What physically happens to old EV batteries when they degrade beyond 70% capacity?"),
    ("Expert", "Can I legally and safely install a 7kW AC fast charger in a typical Indian apartment parking lot?"),
    ("Expert", "Are solid-state batteries actually available in any of the EVs sold in India right now, or is that just hype?"),
    ("Expert", "How exactly does a 45-degree ambient temperature affect an EV's real-world highway range?"),
    ("Expert", "What is V2L (Vehicle-to-Load) technology, and do any Indian cars have it?"),
    ("Expert", "What is a CCS2 connector and why does everyone use it?"),
    ("Expert", "whiich is moar range ola s11 or aher?"), # Misspelling handling
    ("Expert", "Recommend a nice petrol car that gives 20kmpl, maybe a Swift."), # Adversarial (Out of DB focus)
    ("Expert", "Tell me the price of a Tesla Model Y in India."), # Out of DB query
    ("Expert", "Is Ratan Tata or Elon Musk the CEO of Tesla?"), # Completely out of context
    ("Expert", "Can my EV power my house during a power cut?"),
    ("Expert", "What's the IP67 rating mean for the Ather 450X battery pack?"),
    ("Expert", "Explain V2V charging to me like I'm a 10 year old."),
    ("Expert", "If I leave my EV parked at the airport for a month, will the battery just drain to zero?"),
    ("Expert", "Do electric cars have gears or a transmission at all?"),
    ("Expert", "What is thermal runaway in an electric vehicle?"),
    ("Expert", "Can I charge my Tata Nexon from a normal 3-pin wall socket at home like my laptop?")
]

async def main():
    db = SessionLocal()
    with open("CHATBOT_100_TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# 🤖 EViq AI RAG Chatbot - 100 Query Simulation\n\n")
        f.write("Testing 100 queries covering Easy (direct), Medium (comparison), Hard (consultative), and Expert/Adversarial (out-of-data/technical).\n\n")

        for i, (cat, q) in enumerate(QUESTIONS, 1):
            req = ChatRequest(message=q, session_id=f"sim-session-{i}")
            try:
                payload = generate_chat_payload(req, db)
                ans = payload.get("answer", "")
            except Exception as e:
                ans = f"[ERROR ENCOUNTERED]: {e}"
            
            f.write(f"### Q{i}: {q} \n")
            f.write(f"*(**Level:** {cat})*\n\n")
            f.write(f"**🤖 AI:** {ans}\n\n")
            f.write("---\n\n")
            
            q_safe = q.replace('₹', 'Rs.')
            print(f"[{i}/100] Processed: {q_safe[:50]}...")
            
    db.close()
    print("\n✅ Simulation complete. Results saved to CHATBOT_100_TEST_REPORT.md")

if __name__ == "__main__":
    asyncio.run(main())
