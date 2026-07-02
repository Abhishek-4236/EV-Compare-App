# API Guide

The backend runs at `http://127.0.0.1:8000` by default. Interactive docs are available at `http://127.0.0.1:8000/docs`.

## Health

- `GET /health`: verifies the backend process is running.

## Vehicles

- `GET /api/vehicles`: list vehicles.
- `GET /api/vehicles/{id}`: get one vehicle.

## Compare

- `POST /api/compare`: compare selected vehicle IDs.

## Recommendations

- `POST /api/recommend`: recommend vehicles from preferences and filters.

## Chat

- `POST /api/chat`: send a strict dataset-backed EV question.
- `POST /api/chat/stream`: stream a response when supported by the frontend flow.
- Chat answers must stay grounded in repository data; unsupported prompts should return `Not enough data available`.

## Subsidies

- `GET /api/subsidies`: list subsidy guidance.
- Additional subsidy routes are implemented in `backend/routes/subsidies.py`.

## Map And Route Planning

- `GET /api/map/stations`: charging station data.
- `POST /api/map/route-plan`: estimate route and charging stops from bundled data.

## Auth

- `POST /api/auth/signup`: register.
- `POST /api/auth/login`: log in.
- `GET /api/auth/me`: get current user from bearer token.

## Garage And Admin

Garage routes require authentication. Admin routes require an admin role. See route files in `backend/routes/` for exact request bodies and response shapes.
