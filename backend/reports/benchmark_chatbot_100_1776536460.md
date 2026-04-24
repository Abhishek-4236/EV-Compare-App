# EV Chatbot 100-Question Benchmark

- Accuracy: 87.0%
- Passed: 87/100
- Average latency: 32.87 ms

## By Difficulty
- Easy: 25/25 (100.0%), avg 42.17 ms
- Mid: 17/25 (68.0%), avg 28.05 ms
- Hard: 24/25 (96.0%), avg 40.05 ms
- Expert: 21/25 (84.0%), avg 21.19 ms

## By Style
- Direct: 42/50 (84.0%), avg 35.11 ms
- Vague: 24/25 (96.0%), avg 40.05 ms
- Indirect: 21/25 (84.0%), avg 21.19 ms

## Sample Results
- `What is the price of Ola S1 Pro?` -> PASS in 26.35 ms
  Ola S1 Pro. Price: ₹130,000
- `Tell me the range of Ather 450X.` -> PASS in 19.43 ms
  Ather Rizta Z. Range: 160 km
- `Battery capacity of TVS iQube?` -> PASS in 19.45 ms
  TVS iQube. Battery: 3.4 kWh
- `What is the charging time of Bajaj Chetak?` -> PASS in 40.68 ms
  Bajaj Chetak. Charging: 4-6 hrs
- `How much does Hero Vida V1 cost?` -> PASS in 29.5 ms
  Here are the closest EV matches from the current dataset: - Hero Vida V1: ₹120,000, 165 km range, 3.9 kWh battery, charging 4-6 hrs - Hero Vida VX2 Go: ₹110,000, 92 km range, 3.4 kWh battery, charging 4-6 hrs - Hero Vida
- `Tata Nexon EV price and range` -> PASS in 20.1 ms
  Tata Nexon EV. Price: ₹1,650,000. Range: 460 km
- `MG ZS EV battery details` -> PASS in 41.65 ms
  MG ZS EV. Battery: 50.3 kWh
- `Mahindra XUV400 charging type` -> PASS in 17.78 ms
  Mahindra XUV400. Charging: 7 hr / 1.5 hr DC

## Failed Cases
- [mid/direct] `Compare Ola S1 Pro vs Ather 450X` -> | Vehicle | Type | Price | Range | Battery | Charging | |---|---|---:|---:|---:|---| | Ola S1 Pro | scooter | ₹130,000 | 176 km | 4.0 kWh | 4-6 hrs | | Ola S1 Air | scooter | ₹121,000 | 151 km | 4.0 kWh | 4-6 hrs |
- [mid/direct] `Ather Rizta Z vs TVS iQube comparison` -> | Vehicle | Type | Price | Range | Battery | Charging | |---|---|---:|---:|---:|---| | Ather Rizta Z | scooter | ₹186,000 | 160 km | 3.7 kWh | 4-6 hrs | | Ather Rizta S | scooter | ₹140,000 | 123 km | 2.9 kWh | 4-6 hrs |
- [mid/direct] `Compare Tata Tiago EV against MG Comet EV` -> | Vehicle | Type | Price | Range | Battery | Charging | |---|---|---:|---:|---:|---| | Tata Tiago EV | hatchback | ₹2,082,182 | 490 km | 22.68 kWh | 8 hr / 1 hr DC | | Tata Tiago EV XE MR | hatchback | ₹800,000 | 250 km 
- [mid/direct] `Show me a side-by-side for Ioniq 5 and EV6` -> Here are the closest EV matches from the current dataset: - Hyundai Ioniq 5 N: ₹4,650,000, 352 km range, 84.0 kWh battery, charging 7 hrs AC/0.5-1 hrs DC - Omega Seiki Rage+: ₹370,000, 120 km range, 10.8 kWh battery, cha
- [mid/direct] `Nexon EV vs XUV400 which one looks stronger on paper?` -> | Vehicle | Type | Price | Range | Battery | Charging | |---|---|---:|---:|---:|---| | Tata Nexon EV | car | ₹1,650,000 | 460 km | 40.5 kWh | 6-8 hrs AC / 1 hr DC | | Euler Motors Turbo EV 1000 | mini truck | ₹600,000 | 
- [mid/direct] `Could you compare Ather 450X with TVS iQube?` -> | Vehicle | Type | Price | Range | Battery | Charging | |---|---|---:|---:|---:|---| | Ather 450X | scooter | ₹147,000 | 161 km | 2.9 kWh | 4-6 hrs | | Ather Rizta Z | scooter | ₹186,000 | 160 km | 3.7 kWh | 4-6 hrs |
- [mid/direct] `Need a quick comparison of Ather Rizta Z and Ola S1 X` -> Here are the closest EV matches from the current dataset: - Ather Rizta Z: ₹186,000, 160 km range, 3.7 kWh battery, charging 4-6 hrs - Ather Rizta S: ₹140,000, 123 km range, 2.9 kWh battery, charging 4-6 hrs - Ola Roadst
- [mid/direct] `How does Hyundai Ioniq 5 compare with BYD Seal?` -> | Vehicle | Type | Price | Range | Battery | Charging | |---|---|---:|---:|---:|---| | Hyundai Ioniq 5 N | hatchback | ₹4,650,000 | 352 km | 84.0 kWh | 7 hrs AC/0.5-1 hrs DC | | Hyundai creta EV | car | ₹2,500,000 | 510 
- [hard/vague] `Electric vehicle for family of five under 15 lakh` -> Here are the closest EV matches from the current dataset: - Mahindra Electric Treo Zor: ₹347,848, 130 km range, 10.24 kWh battery, charging 4 hr - Hero Electric Flash: ₹63,100, 85 km range, 1.54 kWh battery, charging 4-6
- [expert/indirect] `best ev` -> Here are the closest EV matches from the current dataset: - Tata Xpres T EV: ₹1,374,557, 391 km range, 32.0 kWh battery, charging 4.6hr/ 30 min DC - MG ZS EV: ₹2,202,300, 461 km range, 50.3 kWh battery, charging 9 hr / 1
- [expert/indirect] `which one should i buy?` -> Here are the closest EV matches from the current dataset: - Okinawa OKHI-90: ₹158,500, 160 km range, 3.6 kWh battery, charging 4-6 hrs - Mahindra BE 6: ₹2,200,000, 620 km range, 59.0 kWh battery, charging 6-8 hrs AC / 1 
- [expert/indirect] `give me specs` -> Here are the closest EV matches from the current dataset: - MG ZS EV: ₹2,202,300, 461 km range, 50.3 kWh battery, charging 9 hr / 1 hr DC - MG Windsor EV: ₹2,030,000, 449 km range, 52.9 kWh battery, charging 9.5 hr / 1 h
- [expert/indirect] `What is its top speed?` -> Tata Nexon EV. Top speed: 120.0