# API & Frontend Contract

This document maps the FastAPI backend routes to the UI elements in the React/Vite frontend.

## Backend Routers

1. **`auth.py`**
   - **Frontend:** AuthContext, Login/Register modals (pending UI).
   - **Purpose:** JWT generation, refresh, user creation.

2. **`vehicles.py`**
   - **Frontend:** `BrowsePage.jsx`, `VehicleDetailPage.jsx`
   - **Purpose:** Listing EVs, filtering, pagination, fetching single vehicle details.

3. **`compare.py`**
   - **Frontend:** `ComparePage.jsx`
   - **Purpose:** Returns a normalized payload comparing 2-3 requested vehicle IDs.

4. **`recommend.py`**
   - **Frontend:** `RecommendPage.jsx`
   - **Purpose:** Accepts parameters (budget, daily km, state) and returns scored vehicle lists.

5. **`chat.py`**
   - **Frontend:** `ChatPage.jsx`
   - **Purpose:** Intents parsing, vector retrieval, domain-specific AI chatbot.

6. **`subsidies.py`**
   - **Frontend:** Used dynamically in `VehicleDetailPage.jsx` & `ComparePage.jsx`
   - **Purpose:** Calculates real-time TCO and exact subsidy deductions by state.

7. **`map.py`**
   - **Frontend:** `StationsPage.jsx`
   - **Purpose:** Geospatial search for charging stations.
