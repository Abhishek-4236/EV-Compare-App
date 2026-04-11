# Data Dictionary

## Core Entities

### `vehicles`
The primary table storing the catalog of EVs.
- **segment**: TWO_WHEELER, THREE_WHEELER, FOUR_WHEELER, etc.
- **brand, model, category, wheel_type**
- **approx_price_inr**: Base cost
- **range_km**: Rated range
- **battery_kwh**: Capacity
- **fame2_subsidy_inr**, **state_subsidy_inr**: Pre-calculated or cached subsidy values.
- **embedding**: Vector field for semantic search.

### `users`
Tracks signed-up users.
- **full_name, email, password_hash**
- **role**: guest, user, admin
- **auth_provider**: Standard email or OAuth.

### `saved_comparisons` [Upcoming]
Allows users to save a custom comparison for later viewing.
- **user_id**: References `users`
- **vehicle_ids**: Array of references to `vehicles`.

### `charging_stations` [Upcoming]
Physical locations of charging points to be plotted on Leaflet.
- **name, provider**
- **latitude, longitude**: Numeric fields for map rendering.
- **connector_types**: E.g., CCS2, CHAdeMO.
- **fast_charging_available**: Boolean.

### `subsidy_rules` [Upcoming]
Dynamic lookup table for calculating subsidies per state rather than static code logic.
- **state**: e.g., Telangana, Delhi
- **segment**: Vehicle category
- **subsidy_per_kwh**, **max_subsidy**: Numeric limits based on policy.

### `chat_sessions` & `chat_messages`
Stores historical domain conversation for the user.
- **session_id**, **user_id**
- **role** (user/assistant) and **content**.
