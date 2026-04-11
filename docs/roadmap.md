# EV-Compare-App Roadmap

This document outlines the 16-step roadmap towards a production-ready EV platform.

## Phase 1: Planning and Foundation (In Progress)
- [x] Audit current backend routes and match each to a real frontend page.
- [x] Create a feature matrix.
- [x] Normalize EV data fields from the Excel file in the schema.
- [x] Decide user roles: guest, registered user, admin.
- [x] Decide external providers: maps (Leaflet/OSM), LLM (Ollama), DB (Postgres/pgvector).
- [x] Add `.env.example` for all secrets and config.

## Phase 2: Data Pipeline First (In Progress)
- [ ] Convert `India_EV_All_Segments_Dataset_2026.xlsx` into a reproducible ETL pipeline.
- [ ] Create Python script that validates columns, cleans units, standardizes brands, and loads into Postgres.
- [ ] Add derived fields: price_onroad_est, cost_per_km, fast_charge_supported.
- [ ] Store source metadata.

## Phase 3: Backend Completion (Pending)
- [ ] Refactor FastAPI routes.
- [ ] Setup full JWT Auth.
- [ ] Add pagination / searching.
- [ ] Solidify `/api/compare` and `/api/recommend`.

## Phases 4-16 (Pending)
- Recommendation Engine
- Chatbot Design
- Frontend Completion
- EV Comparison Experience
- TCO and Subsidy Engine
- Charging Stations Map
- UI & UX Redesign
- SEO & PWA
- Performance Optimization
- Testing
- Security
- Production Deployment
- Monitoring
