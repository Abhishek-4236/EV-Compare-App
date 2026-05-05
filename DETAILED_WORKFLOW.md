# 🔋 EV Compare App - Complete Workflow Documentation

**Project**: India EV Comparison & Recommendation Web Application  
**Team**: Sony Anand Kumar, Shaik Zaheer, Sawanth Abhishek  
**Institution**: Vignana Bharathi Institute of Technology (VBIT)  
**Date**: May 2026  
**Purpose**: Research Paper, Documentation & Presentation  

---

## 📑 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technologies Stack](#technologies-stack)
4. [Complete Feature Catalog](#complete-feature-catalog)
5. [Frontend Pages & Components](#frontend-pages--components)
6. [Backend Services & Architecture](#backend-services--architecture)
7. [API Health Check & Analysis](#api-health-check--analysis)
8. [Complete Data Flow](#complete-data-flow)
9. [Server-Side Logic](#server-side-logic)
10. [Frontend-Backend Connection](#frontend-backend-connection)
11. [Advanced Features](#advanced-features)
12. [Testing & Quality Assurance](#testing--quality-assurance)
13. [Utility Scripts & Tools](#utility-scripts--tools)
14. [Knowledge Base & Articles](#knowledge-base--articles)
15. [Feature Workflows](#feature-workflows)
16. [Database Schema](#database-schema)
17. [Configuration & Environment](#configuration--environment)
18. [Deployment & Setup](#deployment--setup)

---

## 1. Project Overview

### Purpose
The EV Compare App is an intelligent web application that enables Indian consumers to make informed decisions about electric vehicles. The platform provides comprehensive comparison tools, AI-powered recommendations, subsidy calculations, and charging station navigation.

### Key Features
✅ **Browse & Filter EVs** - Search 50+ Indian EV models across 5 segments (2W, 3W, 4W, Truck, Bus)  
✅ **Smart Comparison** - Compare 2-4 vehicles side-by-side with value scoring  
✅ **AI-Powered Chat** - Semantic search with RAG (Retrieval-Augmented Generation)  
✅ **Cost Recommendation** - AI recommends vehicles based on budget, daily km, and priority  
✅ **Subsidy Calculator** - Real-time FAME II + State subsidy deductions by state  
✅ **Charging Route Planning** - Find charging stations and plan inter-city trips  
✅ **Garage/Favorites** - Save and organize vehicle comparisons (Auth required)  
✅ **Admin Dashboard** - Upload vehicle data via Excel  

### Target Users
- Individual EV buyers
- Commercial fleet managers
- Policy researchers
- Automotive industry analysts

---

## 4. Complete Feature Catalog

### Core Modules (8 Major Feature Sets)

| Feature | Purpose | Technology | Status |
|---------|---------|-----------|--------|
| **Vehicle Browse** | Search, filter, paginate 50+ EV models | SQL + React Query | ✅ Active |
| **AI Chat Assistant** | Semantic Q&A with RAG pipeline | FAISS + LLM + Embeddings | ✅ Active |
| **Vehicle Comparison** | Side-by-side specs + value scoring | Weighted algorithms | ✅ Active |
| **Smart Recommendation** | Budget-based intelligent suggestions | Multi-factor scoring | ✅ Active |
| **Subsidy Calculator** | Real-time FAME II + State incentives | Policy database + calc | ✅ Active |
| **Charging Map** | Station finder + route planning | Geospatial + Haversine | ✅ Active |
| **TCO Calculator** | 5-year cost comparison (EV vs Petrol) | Financial calculations | ✅ Active |
| **User Garage** | Save & organize comparisons | User-specific storage | ✅ Active |

### Additional Capabilities

- **User Authentication** - Email/password signup, JWT tokens, session management
- **Admin Dashboard** - Excel dataset upload, statistics, user analytics
- **Chat Memory** - Persistent session history with message tracking
- **Feedback System** - User ratings on chat responses (👍/👎)
- **Session Management** - Independent chat sessions per user
- **Data Export** - Comparison results and recommendations

---

## 5. Frontend Pages & Components

### Pages (12 Total)

| Page | Route | Purpose | Features |
|------|-------|---------|----------|
| **HomePage** | `/` | Landing & hero section | Featured vehicles, CTA buttons, stats |
| **AuthPage** | `/login` | Authentication | Signup, login, JWT handling |
| **BrowsePage** | `/browse` | Vehicle listing | Filters, pagination, grid view |
| **VehicleDetailPage** | `/vehicle/:id` | Single vehicle view | Full specs, related articles, subsidy calc |
| **ComparePage** | `/compare` | Multi-vehicle comparison | Side-by-side table, charts, save to garage |
| **ChatPage** | `/chat` | AI assistant interface | Streaming responses, session history, feedback |
| **RecommendPage** | `/recommend` | Smart recommendations | Wizard form, budget filter, priority-based ranking |
| **SubsidiesPage** | `/subsidies` | Subsidy information | State-wise breakdown, policy details |
| **TcoPage** | `/tco` | Total cost calculator | 5-year financial analysis (EV vs Petrol) |
| **ChargingMapPage** | `/map` | Charging stations | Map view, route planning, geospatial search |
| **GaragePage** | `/garage` | Saved comparisons | User's saved vehicle sets, delete, organize |
| **AdminPage** | `/admin` | Admin dashboard | Excel upload, statistics, data management |

### Reusable Components (15+)

| Component | Purpose | Location |
|-----------|---------|----------|
| **Navbar** | Navigation header | `components/Navbar.jsx` |
| **Footer** | Site footer | `components/Footer.jsx` |
| **VehicleCard** | Vehicle display card | `components/VehicleCard.jsx` |
| **CompareBar** | Persistent compare selection bar | `components/CompareBar.jsx` |
| **ChatComposer** | Chat input box | `components/chat/ChatComposer.jsx` |
| **ChatMessage** | Single chat message display | `components/chat/ChatMessage.jsx` |
| **ChatSidebar** | Chat session history sidebar | `components/chat/ChatSidebar.jsx` |
| **TypingIndicator** | Animated typing animation | `components/chat/TypingIndicator.jsx` |
| **CompareDrawer** | Slide-out compare panel | `components/CompareDrawer/` |
| **SegmentTabs** | Vehicle segment switcher | `components/SegmentTabs/` |
| **TCOCalculator** | EV vs Petrol cost widget | `components/TCOCalculator/` |
| **Charts** | Data visualization suite | `components/charts/` |
| **ChatWidget** | Embedded chat component | `components/ChatWidget/` |

---

## 2. System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React.js + Vite)                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Pages: Home, Browse, Compare, Chat, Recommend, Subsidies,   │   │
│  │ TCO, Charging Map, Admin, Auth, Garage                       │   │
│  │                                                               │   │
│  │ Components: Navbar, ChatWidget, CompareBar, VehicleCard,    │   │
│  │ Charts, Tabs, Drawers                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                    HTTP/HTTPS API Calls                            │
│                    (Axios + React Query)                           │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   CORS Middleware   │
                    │   (FastAPI)         │
                    └──────────┬──────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                         │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     API ROUTERS (8 modules)                    │  │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │  │
│  │ │ /api/auth    │ │ /api/vehicles│ │ /api/compare         │   │  │
│  │ │ - Signup     │ │ - Browse     │ │ - Compare 2-4 cars   │   │  │
│  │ │ - Login      │ │ - Filter     │ │ - Value scoring      │   │  │
│  │ │ - JWT Token  │ │ - Pagination │ │ - Efficiency calc    │   │  │
│  │ └──────────────┘ └──────────────┘ └──────────────────────┘   │  │
│  │                                                                │  │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │  │
│  │ │ /api/chat    │ │ /api/recommend    │ /api/subsidies   │   │  │
│  │ │ - RAG Pipeline│ │ - Smart recomm.  │ - FAME II subsidy│   │  │
│  │ │ - Sessions   │ │ - Budget filter  │ - State subsidy  │   │  │
│  │ │ - Streaming  │ │ - Priority-based │ - TCO calculation│   │  │
│  │ │ - Feedback   │ │ - Segment filter │ - Policy meta    │   │  │
│  │ └──────────────┘ └──────────────────┘ └──────────────────────┘   │  │
│  │                                                                │  │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │  │
│  │ │ /api/map     │ │ /api/garage  │ │ /api/admin           │   │  │
│  │ │ - Stations   │ │ - Save comps │ │ - Upload Excel       │   │  │
│  │ │ - Route plan │ │ - Delete     │ │ - Stats/Dashboard    │   │  │
│  │ │ - Haversine  │ │ - Retrieve   │ │ - Auth required      │   │  │
│  │ │ - Geospatial │ │ - Auth reqd. │ │                      │   │  │
│  │ └──────────────┘ └──────────────┘ └──────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                               │                                       │
│  ┌────────────────────────────▼───────────────────────────────────┐  │
│  │              BUSINESS LOGIC SERVICES (services/)              │  │
│  │ ┌──────────────────────────────────────────────────────────┐  │  │
│  │ │ • ev_rag.py - RAG Pipeline (Vector + LLM retrieval)      │  │  │
│  │ │ • query_parser.py - Intent parsing & filter extraction   │  │  │
│  │ │ • embeddings.py - OpenAI embeddings generation           │  │  │
│  │ │ • ev_chat_response.py - Answer generation with sources   │  │  │
│  │ │ • ev_chat_memory.py - Session memory & context           │  │  │
│  │ │ • ev_policy.py - Subsidy rules & policy engine           │  │  │
│  │ │ • llm.py - LLM provider configuration                    │  │  │
│  │ │ • nvidia_reranker.py - Optional NVIDIA reranking         │  │  │
│  │ └──────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                               │                                       │
└───────────────────────────────┼───────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐   ┌───────────────────┐   ┌──────────────┐
│   PostgreSQL     │   │  FAISS Vector DB  │   │  File System │
│   (SQLAlchemy)   │   │  (Knowledge Index)│   │  (uploaded   │
│                  │   │                   │   │   data)      │
│ • Vehicles       │   │ • Chunks embed    │   │              │
│ • Users          │   │ • Similarity      │   │ • Articles   │
│ • Chat Sessions  │   │ • Fast retrieval  │   │ • Excel Data │
│ • Saved Comps    │   │ • Re-ranking      │   │              │
│ • Subsidies      │   │ (optional NVIDIA) │   │              │
└──────────────────┘   └───────────────────┘   └──────────────┘
```

---

## 3. Technologies Stack

### **Frontend Stack**
| Technology | Purpose | Version |
|-----------|---------|---------|
| **React.js** | UI Library & component framework | 19.2.4 |
| **Vite** | Lightning-fast build tool | 8.0.1 |
| **React Router DOM** | Client-side routing | 7.13.1 |
| **Axios** | HTTP client for API calls | 1.13.6 |
| **React Query (@tanstack)** | Server state management | 5.97.0 |
| **Zustand** | Lightweight state management | 5.0.12 |
| **Chart.js** | Data visualization library | 4.5.1 |
| **Leaflet** | Interactive mapping | 1.9.4 |
| **React Leaflet** | React wrapper for Leaflet | 5.0.0 |
| **Framer Motion** | Smooth animations | 12.38.0 |
| **Tailwind CSS** | Utility-first CSS framework | 4.2.2 |
| **React Markdown** | Markdown rendering | 10.1.0 |
| **Lucide React** | Icon library | 1.8.0 |

### **Backend Stack**
| Technology | Purpose | Version |
|-----------|---------|---------|
| **FastAPI** | Modern async web framework | 0.135.1 |
| **Python** | Server-side language | 3.11+ |
| **SQLAlchemy** | ORM for database operations | 2.0.48 |
| **PostgreSQL** | Relational database | 12+ |
| **psycopg2** | PostgreSQL adapter for Python | 2.9.11 |
| **PGVector** | Vector storage in PostgreSQL | Latest |
| **asyncpg** | Async PostgreSQL driver | Latest |
| **Uvicorn** | ASGI server | 0.41.0 |
| **Pydantic** | Data validation & serialization | 2.12.5 |
| **OpenAI** | LLM API integration | Latest |
| **Google GenAI** | Alternative LLM provider | Latest |
| **Sentence-Transformers** | Embedding generation | Latest |
| **FAISS** | Vector similarity search | Latest |
| **Passlib** | Password hashing | Latest |
| **PyJWT** | JWT token handling | Latest |
| **python-jose** | JWT cryptography | Latest |
| **redis** | Caching & session storage (optional) | Latest |
| **Pandas** | Data processing | Latest |
| **openpyxl** | Excel file parsing | Latest |

### **DevOps & Deployment**
| Technology | Purpose |
|-----------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Git** | Version control |
| **Pytest** | Python testing framework |

---

## 6. Backend Services & Architecture

### Service Modules (18 Services)

#### RAG & NLP Services
| Service | Purpose | Key Classes |
|---------|---------|------------|
| **ev_rag.py** | Core RAG pipeline orchestrator | `EVRAGService` - main inference engine |
| **query_parser.py** | Natural language intent parsing | Extracts filters, budget, vehicle types from user queries |
| **ev_chat_response.py** | Answer generation builder | Constructs contextual answers with sources |
| **ev_chat_retrieval.py** | Hybrid retrieval (vector + SQL) | `hybrid_retrieve()` - combines semantic + structured search |
| **ev_chat_memory.py** | Conversation context management | Session memory, user level tracking, clarification logic |
| **ev_chat_knowledge.py** | Knowledge article retrieval | Domain knowledge Q&A (about charging, batteries, policy) |
| **faiss_store.py** | Vector index management | `FaissStore` - FAISS wrapper for similarity search |

#### Embedding & Language Model Services
| Service | Purpose | Key Classes |
|---------|---------|------------|
| **embeddings.py** | Text embedding generation | `start_model_warmup()` - Sentence-Transformers (all-MiniLM-L6-v2) |
| **llm.py** | LLM provider abstraction | Supports OpenAI, Groq, HuggingFace, Gemini |
| **openai_client.py** | OpenAI API wrapper | Custom client for chat/embedding calls |
| **nvidia_reranker.py** | Optional NVIDIA reranking | Improves retrieval ranking if enabled |

#### Data & Catalog Services
| Service | Purpose | Key Classes |
|---------|---------|------------|
| **ev_catalog.py** | Vehicle data normalization | `VehicleDocument` - converts Excel rows to structured documents |
| **ev_policy.py** | Subsidy policy engine | State-wise subsidy lookup and TCO calculations |
| **data_cleaning.py** | Data preprocessing | Handles missing values, normalization, validation |
| **chat_analysis.py** | Chat quality metrics | Analyzes conversation patterns, intents |

#### Utility Services
| Service | Purpose | Key Classes |
|---------|---------|------------|
| **startup_sync.py** | Startup health checks | `ensure_data_ready_on_startup()` - validates all systems |
| **retrieval.py** | Generic retrieval utilities | Station finders, distance calculations |
| **ev_rag_types.py** | Type definitions | `ParsedQuery`, `ChatAnswer`, `VehicleDocument`, `RetrievalMatch` |

### Service Dependencies Flow

```
User Query
    ↓
query_parser.py (Intent extraction)
    ↓
ev_chat_retrieval.py (Hybrid search)
    ├─ Vector search (FAISS)
    ├─ SQL filtering
    └─ Optional NVIDIA reranking
    ↓
ev_chat_memory.py (Context building)
    ├─ Session history
    └─ Clarification logic
    ↓
llm.py (LLM generation)
    ├─ OpenAI, Groq, HF, Gemini
    └─ Streaming or buffered
    ↓
ev_chat_response.py (Answer formatting)
    ├─ Add sources
    ├─ Include metadata
    └─ Format for frontend
    ↓
Chat Response (with matches & confidence)
```

---

## 4. API Health Check & Analysis

### 4.1 Health Endpoint

```python
@app.get("/health")
def health():
    return {
        "status": "OK",
        "project": "India EV Compare",
        "team": "VBIT"
    }
```

**Purpose**: Verifies backend is running  
**Response**: `200 OK`  
**Used**: ✅ Yes (startup checks, monitoring)

---

### 4.2 Complete API Endpoint Analysis

#### **✅ AUTHENTICATION ROUTER** (`/api/auth`)

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/signup` | POST | User registration with email/password | ❌ | ✅ **USED** | AuthPage.jsx |
| `/login` | POST | JWT token generation | ❌ | ✅ **USED** | AuthPage.jsx |
| `/me` | GET | Fetch current user profile | ✅ Bearer | ✅ **USED** | useAuth hook |
| `/google/config` | GET | Google OAuth config | ❌ | ⚠️ **PARTIAL** | Auth setup only |

---

#### **✅ VEHICLES ROUTER** (`/api/vehicles`)

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/meta/brands` | GET | Fetch all available brands | ❌ | ✅ **USED** | BrowsePage (filters) |
| `/` | GET | Browse vehicles with filters | ❌ | ✅ **USED** | BrowsePage.jsx |
| `/featured/diverse` | GET | Homepage featured diverse EVs | ❌ | ✅ **USED** | HomePage.jsx |
| `/{vehicle_id}` | GET | Vehicle detail page | ❌ | ✅ **USED** | VehicleDetailPage.jsx |

**Query Parameters** (for `/`):
- `category` - Filter by 2W, 3W, 4W, Truck, Bus
- `brand` - Filter by manufacturer
- `min_price`, `max_price` - Price range
- `min_range`, `max_range` - Range in km
- `charging_type` - AC, DC, or both
- `sort_by` - approx_price_inr, range_km, overall_rating, battery_kwh, top_speed_kmh
- `sort_order` - ASC or DESC
- `page`, `limit` - Pagination

---

#### **✅ COMPARE ROUTER** (`/api/compare`)

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/` | POST | Compare 2-4 vehicles | ❌ | ✅ **USED** | ComparePage.jsx |

**Request Body**:
```json
{
  "ids": [12, 15, 20]
}
```

**Response Includes**:
- Vehicle specs (price, range, battery, speed)
- Cost efficiency (range/price ratio)
- Value score (weighted scoring)
- FAME II subsidy
- All comparable specs

---

#### **✅ RECOMMEND ROUTER** (`/api/recommend`)

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/` | POST | Smart vehicle recommendation | ❌ | ✅ **USED** | RecommendPage.jsx |

**Request Body**:
```json
{
  "budget": 1500000,
  "daily_km": 50,
  "segment": "car",
  "priority": "range"
}
```

**Priority Weights**:
- `"range"` → Range: 50%, Price: 25%, Speed: 25%
- `"price"` → Range: 25%, Price: 50%, Speed: 25%
- `"speed"` → Range: 25%, Price: 25%, Speed: 50%

---

#### **✅ CHAT ROUTER** (`/api/chat`) - **Core AI Feature**

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/` | POST | Send chat message (buffered response) | ⚠️ Optional | ✅ **USED** | ChatPage.jsx |
| `/stream` | POST | Streaming response (SSE) | ⚠️ Optional | ✅ **USED** | ChatPage.jsx |
| `/feedback` | POST | Rate chat response helpfulness | ⚠️ Optional | ✅ **USED** | ChatMessage.jsx |
| `/sessions` | GET | Fetch user's chat history | ✅ Required | ✅ **USED** | ChatSidebar.jsx |
| `/sessions/{id}` | PUT | Rename chat session | ✅ Required | ✅ **USED** | ChatSidebar.jsx |
| `/sessions/{id}` | DELETE | Delete chat session | ✅ Required | ✅ **USED** | ChatSidebar.jsx |
| `/history/{session_id}` | GET | Get chat messages in session | ❌ | ✅ **USED** | ChatPage.jsx |
| `/provider-status` | GET | Check LLM provider health | ❌ | ✅ **USED** | Chat setup |

**RAG Pipeline** (Retrieval-Augmented Generation):
1. User sends query
2. Query parser extracts intent & filters
3. Vector search retrieves relevant vehicles
4. Optional NVIDIA reranking
5. LLM generates response with sources
6. Streaming or buffered response to frontend

---

#### **✅ SUBSIDIES ROUTER** (`/api/subsidies`)

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/` | GET | Calculate subsidy for vehicle+state | ❌ | ✅ **USED** | ComparePage, VehicleDetail |
| `/policy` | GET | Fetch subsidy policy metadata | ❌ | ✅ **USED** | SubsidiesPage.jsx |

**Request Parameters**:
- `vehicle_id` - Vehicle ID
- `state` - Indian state name (lowercase)

**Calculation Logic**:
1. FAME II subsidy (fixed per vehicle)
2. State-specific subsidy lookup
3. Tax impact considerations
4. Returns: `(price - fame2 - state_subsidy)`

---

#### **✅ MAP ROUTER** (`/api/map`)

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/stations` | GET | Fetch charging stations by city | ❌ | ✅ **USED** | ChargingMapPage.jsx |
| `/route-plan` | POST | Plan inter-city charging route | ❌ | ✅ **USED** | ChargingMapPage.jsx |

**`/stations` Parameters**:
- `city` - Optional (returns all if null)

**`/route-plan` Body**:
```json
{
  "source": "Delhi",
  "destination": "Jaipur",
  "range_km": 300,
  "start_soc_percent": 90,
  "reserve_percent": 15
}
```

**Algorithm**: Haversine distance formula with optimized station placement

---

#### **✅ GARAGE ROUTER** (`/api/garage`) - Saved Comparisons

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/` | GET | Fetch user's saved comparisons | ✅ Required | ✅ **USED** | GaragePage.jsx |
| `/` | POST | Save a new comparison | ✅ Required | ✅ **USED** | ComparePage.jsx |
| `/{save_id}` | DELETE | Remove saved comparison | ✅ Required | ✅ **USED** | GaragePage.jsx |

---

#### **✅ ADMIN ROUTER** (`/api/admin`)

| Endpoint | Method | Purpose | Auth | Status | Frontend |
|----------|--------|---------|------|--------|----------|
| `/upload-dataset` | POST | Upload vehicle Excel file | ✅ Admin | ✅ **USED** | AdminPage.jsx |
| `/stats` | GET | Dashboard statistics | ✅ Admin | ✅ **USED** | AdminPage.jsx |

**Admin Requirements**:
- User must have `role = "admin"`
- JWT token required

---

### 4.3 Unused/Deprecated APIs

❌ **NONE IDENTIFIED** - All endpoints are actively used in the frontend or for internal functionality.

However, the following are **PARTIALLY USED**:
- `/api/auth/google/config` - OAuth setup exists but not fully implemented in UI

---

## 7. Complete Data Flow

### 5.1 User Registration & Authentication Flow

```
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: User lands on Login/Signup page                       │
│  ↓                                                              │
│  Frontend: <AuthPage /> renders form                           │
│  • Full name, Email, Password (min 8 chars)                   │
│                                                                │
│  ↓ (User fills form & clicks SIGNUP)                          │
│                                                                │
│  STEP 2: Frontend POST /api/auth/signup                       │
│  Request:                                                      │
│  {                                                             │
│    "full_name": "Arun Kumar",                                │
│    "email": "arun@example.com",                              │
│    "password": "SecurePass123"                               │
│  }                                                             │
│                                                                │
│  ↓                                                              │
│  STEP 3: Backend Validation & Hashing                        │
│  • Check password >= 8 chars                                 │
│  • Query: SELECT * FROM users WHERE email = lower(email)    │
│  • If exists: HTTP 409 Conflict "Email already registered"  │
│  • Hash password using pbkdf2_sha256                         │
│                                                                │
│  ↓                                                              │
│  STEP 4: Create User in DB                                   │
│  INSERT INTO users (full_name, email, password_hash,         │
│                     auth_provider, role, created_at)         │
│  VALUES ('Arun Kumar', 'arun@example.com',                   │
│          'hashed_pwd', 'email', 'user', NOW())               │
│                                                                │
│  ↓                                                              │
│  STEP 5: JWT Token Generation                                │
│  Algorithm: HS256                                            │
│  Payload: {                                                   │
│    "sub": "123",           # user_id                         │
│    "exp": "2026-05-05..."  # expires in 30 mins             │
│  }                                                             │
│  Secret: JWT_SECRET from .env                                │
│                                                                │
│  ↓                                                              │
│  STEP 6: Response to Frontend                                │
│  {                                                             │
│    "success": true,                                           │
│    "access_token": "eyJhbGc...",                             │
│    "token_type": "bearer",                                    │
│    "user": {                                                   │
│      "id": 123,                                               │
│      "full_name": "Arun Kumar",                              │
│      "email": "arun@example.com",                            │
│      "auth_provider": "email"                                │
│    }                                                           │
│  }                                                             │
│                                                                │
│  ↓                                                              │
│  STEP 7: Frontend Storage                                    │
│  • Zustand useAuth store: setToken(), setUser()             │
│  • Store in localStorage: "auth_token"                       │
│  • Redirect to HomePage                                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Vehicle Browse & Filter Flow

```
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: User navigates to /browse (BrowsePage.jsx)           │
│                                                                │
│  ↓                                                              │
│  STEP 2: Load Filter Options                                  │
│  Frontend: GET /api/vehicles/meta/brands                      │
│  Response: {                                                   │
│    "brands": ["Tesla", "Tata", "Mahindra", "Ather", ...]     │
│  }                                                             │
│                                                                │
│  ↓                                                              │
│  STEP 3: User Interacts with Filters                         │
│  • Select category: "4W"                                      │
│  • Select brand: "Tata"                                       │
│  • Set price range: ₹10L - ₹25L                              │
│  • Set range: 300km - 500km                                  │
│  • Select charging: "DC Fast Charging"                        │
│  • Sort by: "overall_rating" (DESC)                          │
│                                                                │
│  ↓ (Auto-debounced API call, 300ms delay)                    │
│                                                                │
│  STEP 4: Frontend GET /api/vehicles/                          │
│  Query String:                                                │
│  ?category=4W&brand=Tata&min_price=1000000&max_price=2500000│
│  &min_range=300&max_range=500&charging_type=DC&              │
│  sort_by=overall_rating&sort_order=DESC&page=1&limit=20      │
│                                                                │
│  ↓                                                              │
│  STEP 5: Backend Query Execution                              │
│  query = SELECT * FROM vehicles WHERE                         │
│    market_status = 'Available' AND                            │
│    category = '4W' AND                                        │
│    brand = 'Tata' AND                                         │
│    approx_price_inr BETWEEN 1000000 AND 2500000 AND          │
│    range_km BETWEEN 300 AND 500 AND                           │
│    charging_type = 'DC' AND                                   │
│    (vehicle_type NOT LIKE '%commercial%' AND ...)           │
│  ORDER BY overall_rating DESC                                 │
│  LIMIT 20 OFFSET 0                                            │
│                                                                │
│  ↓                                                              │
│  STEP 6: Response Structure                                   │
│  {                                                             │
│    "success": true,                                           │
│    "total": 5,     # Total matching vehicles                 │
│    "page": 1,      # Current page                            │
│    "vehicles": [                                              │
│      {                                                         │
│        "id": 42,                                              │
│        "brand": "Tata",                                       │
│        "model": "Nexon EV Max",                              │
│        "category": "4W",                                      │
│        "approx_price_inr": 1875000,                          │
│        "range_km": 440,                                       │
│        "battery_kwh": 75.0,                                   │
│        "charging_type": "DC",                                 │
│        "overall_rating": 4.5,                                │
│        "image_url": "https://...",                           │
│        ... # 15 more fields                                   │
│      },                                                        │
│      ...                                                       │
│    ]                                                           │
│  }                                                             │
│                                                                │
│  ↓                                                              │
│  STEP 7: Frontend Rendering                                  │
│  • Map response array to VehicleCard components              │
│  • Display pagination (5 total, page 1 of 1)                │
│  • Show "5 vehicles found"                                    │
│                                                                │
│  ↓ (User clicks NEXT pagination button for page 2)          │
│  →  Repeat from STEP 4 with page=2                           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 AI Chat RAG Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: User enters query in ChatPage.jsx                          │
│  Example: "Best EV under 15 lakh with fast charging"               │
│                                                                      │
│  ↓                                                                    │
│  STEP 2: Frontend POST /api/chat/                                   │
│  {                                                                   │
│    "message": "Best EV under 15 lakh with fast charging",          │
│    "session_id": "null"  # null = new session                      │
│  }                                                                   │
│                                                                      │
│  ↓                                                                    │
│  STEP 3: Backend Session Management                                 │
│  • If session_id is null, create new ChatSession                   │
│    INSERT INTO chat_sessions (id, title, user_id, expertise_level)│
│    VALUES (uuid(), "Best EV under 15 lakh...", null, 'Novice')    │
│  • Generate title from first 40 chars of message                   │
│  • Optional: Link to user_id if authenticated                      │
│                                                                      │
│  ↓                                                                    │
│  STEP 4: Query Parsing (query_parser.py)                           │
│  OpenAI API Call (gpt-4-mini):                                     │
│  SYSTEM PROMPT: """                                                │
│    You are an EV expert. Parse this query for:                     │
│    - intent: 'recommendation', 'comparison', 'info', etc.         │
│    - filters: price range, km range, vehicle type                 │
│    - sort: price, range, rating                                    │
│  """                                                                │
│                                                                      │
│  USER PROMPT: "Best EV under 15 lakh with fast charging"          │
│                                                                      │
│  RESPONSE (JSON):                                                   │
│  {                                                                   │
│    "intent": "recommendation",                                      │
│    "rewritten_query": "electric vehicle <= 1500000 INR",          │
│    "filters": {                                                     │
│      "max_price_inr": 1500000,                                     │
│      "charging_type": "DC",                                        │
│      "min_range_km": 250                                           │
│    },                                                               │
│    "user_goal": "best EV under 15 lakh with fast charging"        │
│  }                                                                   │
│                                                                      │
│  ↓                                                                    │
│  STEP 5: Vector Search (FAISS) - ev_rag.py                         │
│  • Embed the rewritten_query using Sentence-Transformers          │
│  • Query FAISS index: knowledge.faiss                              │
│  • Retrieve top-5 similar vehicle documents                        │
│                                                                      │
│  ↓                                                                    │
│  STEP 6: Structured Filtering (SQL + Semantic)                     │
│  SELECT * FROM vehicles WHERE                                      │
│    approx_price_inr <= 1500000 AND                                 │
│    (charging_type = 'DC' OR charging_type = 'Both') AND           │
│    range_km >= 250 AND                                              │
│    market_status = 'Available'                                     │
│  LIMIT 10                                                           │
│                                                                      │
│  ↓                                                                    │
│  STEP 7: Optional NVIDIA Reranking                                 │
│  IF NVIDIA_RERANK_ENABLED == true:                                 │
│    Call NVIDIA LLM Reranking API:                                  │
│    - Input: query + candidate passages                             │
│    - Output: reordered by relevance                                │
│  ELSE:                                                               │
│    - Use local similarity scores                                    │
│                                                                      │
│  ↓                                                                    │
│  STEP 8: Context Building                                           │
│  sources = [                                                        │
│    {"id": 42, "name": "Tata Nexon EV", "price": 1450000, ...},   │
│    {"id": 51, "name": "Mahindra XUV400", "price": 1299000, ...},  │
│    ...                                                               │
│  ]                                                                   │
│  context_text = Format sources into readable context               │
│                                                                      │
│  ↓                                                                    │
│  STEP 9: LLM Response Generation                                    │
│  OpenAI API Call (gpt-4-mini or Claude):                           │
│  SYSTEM PROMPT: """                                                │
│    You are a friendly EV buying assistant in India.                │
│    Provide recommendations based on the provided vehicles.         │
│  """                                                                │
│                                                                      │
│  USER PROMPT: """                                                  │
│    User Query: "Best EV under 15 lakh with fast charging"         │
│                                                                      │
│    Available Vehicles:                                              │
│    {context_text}                                                   │
│                                                                      │
│    Provide a helpful recommendation considering budget and charging│
│  """                                                                │
│                                                                      │
│  RESPONSE:                                                          │
│  "Based on your budget of ₹15 lakh and need for fast charging,    │
│   I recommend the Tata Nexon EV (₹14.5L) with 440km range and     │
│   DC fast charging capability. It's one of the best value options │
│   in the market. An alternative is the Mahindra XUV400 (₹12.99L)  │
│   with similar specifications and better pricing."                 │
│                                                                      │
│  ↓                                                                    │
│  STEP 10: Store Chat in Database                                    │
│  INSERT INTO chat_messages (session_id, role, content, created_at)│
│  VALUES (session_uuid, 'user', 'Best EV under 15 lakh...', NOW()) │
│  INSERT INTO chat_messages (session_id, role, content, created_at)│
│  VALUES (session_uuid, 'assistant', 'Based on your budget...', NOW)│
│                                                                      │
│  ↓                                                                    │
│  STEP 11: Response to Frontend                                      │
│  {                                                                   │
│    "success": true,                                                │
│    "session_id": "abc-123-def",                                    │
│    "answer": "Based on your budget of ₹15 lakh...",              │
│    "intent": "recommendation",                                      │
│    "parsed_query": { ... },                                        │
│    "sources": [                                                     │
│      {                                                              │
│        "vehicle_id": 42,                                           │
│        "name": "Tata Nexon EV",                                    │
│        "price": 1450000,                                           │
│        "range_km": 440                                             │
│      },                                                              │
│      ...                                                             │
│    ]                                                                │
│  }                                                                   │
│                                                                      │
│  ↓                                                                    │
│  STEP 12: Frontend Rendering                                        │
│  • Display answer in ChatMessage component                          │
│  • Show sources as clickable vehicle cards                         │
│  • Add thumbs-up/thumbs-down feedback buttons                      │
│  • Store session_id for history continuity                         │
│  • TypingIndicator shows while awaiting response                   │
│                                                                      │
│  ↓ (User asks follow-up: "What about the Tata Nexon pricing?")    │
│  →  Repeat from STEP 4 with same session_id                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.4 Vehicle Comparison Flow

```
┌─────────────────────────────────────────────┐
│  STEP 1: User browses vehicles              │
│  • Clicks "+" button on VehicleCard         │
│  • CompareBar (persistent) shows selections │
│                                              │
│  ↓ (Select 2-4 vehicles)                    │
│                                              │
│  STEP 2: CompareBar state update            │
│  • Zustand useCompare store:                │
│    selectedIds: [12, 25, 38]               │
│                                              │
│  ↓ (Click "View Comparison")                │
│                                              │
│  STEP 3: Navigate to /compare               │
│  • ComparePage.jsx loads                    │
│  • Calls API: POST /api/compare/            │
│                                              │
│  STEP 4: Backend Calculation                │
│  FOR EACH vehicle:                          │
│    cost_efficiency = range / (price/100k)   │
│    value_score = (                          │
│      range * 0.35 +                        │
│      (1/price) * 10M * 0.30 +              │
│      battery * 0.20 +                       │
│      rating * 0.15                          │
│    )                                        │
│                                              │
│  STEP 5: Response Structure                 │
│  {                                           │
│    "success": true,                         │
│    "vehicles": [                            │
│      {                                       │
│        "id": 12,                            │
│        "brand": "Tata",                     │
│        "model": "Nexon EV Max",             │
│        "approx_price_inr": 1875000,         │
│        "range_km": 440,                     │
│        "battery_kwh": 75.0,                 │
│        "charging_type": "DC",               │
│        "overall_rating": 4.5,               │
│        "cost_efficiency": 2.35,             │
│        "value_score": 245.67,               │
│        "fame2_subsidy_inr": 150000          │
│      },                                      │
│      ... (2 more vehicles)                  │
│    ]                                        │
│  }                                           │
│                                              │
│  STEP 6: Frontend Rendering                 │
│  • Create comparison table with all specs   │
│  • Highlight best value_score               │
│  • Show cost_efficiency ranking             │
│  • Add subsidy info from /api/subsidies/    │
│  • Charts: Price vs Range scatter, Rating   │
│  • Bottom action: "Save to Garage"          │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 6. Server-Side Logic

### 6.1 Authentication & Authorization

**File**: `backend/routes/auth.py`

```python
# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"
JWT_EXPIRE_MINUTES = 30

def create_access_token(user_id: str) -> str:
    """Generate JWT token valid for 30 minutes"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_token(token: str) -> int:
    """Extract and validate user_id from JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Password Hashing**: PBKDF2-SHA256 (Passlib)
- Minimum 8 characters required
- Automatically salted & iterated

---

### 6.2 Vehicle Filtering & Pagination

**File**: `backend/routes/vehicles.py`

```python
ALLOWED_SORTS = [
    "approx_price_inr", "range_km", "overall_rating", 
    "battery_kwh", "top_speed_kmh"
]

# Commercial vehicle exclusion (for 4W segment only)
def passenger_car_filter():
    commercial_keywords = [
        "commercial", "cargo", "truck", "mini truck", 
        "scv", "delivery"
    ]
    # Returns OR condition to exclude these types

# Pagination: OFFSET/LIMIT pattern
offset = (page - 1) * limit
vehicles = query.offset(offset).limit(limit).all()
```

---

### 6.3 Query Parser (Intent Detection)

**File**: `backend/services/query_parser.py`

```
User Input: "Best EV under 15 lakh with fast charging"
                    ↓
                OpenAI Call
                    ↓
Parse Output:
{
  "intent": "recommendation",
  "filters": {
    "max_price_inr": 1500000,
    "charging_type": "DC",
  },
  "sort_by": "price",
  "user_goal": "best EV under 15 lakh"
}
                    ↓
Applied in RAG retrieval to filter candidates
```

---

### 6.4 RAG (Retrieval-Augmented Generation) Pipeline

**File**: `backend/services/ev_rag.py`

```python
class EVRAGService:
    def __init__(self):
        # Load FAISS index from preprocessed files
        self.index = faiss.read_index("data/processed/knowledge.faiss")
        self.meta = load_meta("data/processed/knowledge.meta.json")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    def retrieve(self, query: str, k: int = 5):
        # Convert query to embedding
        query_embedding = self.embedder.encode([query])
        
        # FAISS search
        distances, indices = self.index.search(query_embedding, k)
        
        # Get vehicle metadata
        candidates = [self.meta[i] for i in indices[0]]
        
        return candidates  # List of top-5 relevant vehicles
    
    def rerank(self, candidates, query):
        # Optional: Use NVIDIA reranker if enabled
        if settings.NVIDIA_RERANK_ENABLED:
            return nvidia_rerank(candidates, query)
        return candidates
```

---

### 6.5 Subsidy Calculation Logic

**File**: `backend/routes/subsidies.py`

```python
def calculate_subsidies(vehicle_id: int, state: str):
    # Step 1: Get vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    # Step 2: FAME II Subsidy (National)
    fame2_subsidy = vehicle.fame2_subsidy_inr or 0  # Per vehicle
    
    # Step 3: State Subsidy Lookup
    state_subsidy = FALLBACK_STATE_SUBSIDY_MAP.get(state.lower(), 0)
    
    # Step 4: Total Reduction
    original_price = vehicle.approx_price_inr
    final_price = original_price - fame2_subsidy - state_subsidy
    
    return {
        "original_price": original_price,
        "fame2_subsidy": fame2_subsidy,
        "state_subsidy": state_subsidy,
        "final_price": final_price,
        "total_discount_percent": ((fame2_subsidy + state_subsidy) / original_price) * 100
    }
```

---

### 6.6 Geospatial Charging Station Logic

**File**: `backend/routes/map.py`

```python
def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Calculate great-circle distance between two points"""
    R = 6371.0  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return 2 * R * asin(sqrt(a))

def find_optimal_route(source_city, dest_city, vehicle_range_km):
    """Find charging stations along the route"""
    source_coords = resolve_city(source_city)
    dest_coords = resolve_city(dest_city)
    total_distance = haversine_km(*source_coords, *dest_coords)
    
    # Greedy: Find stations along the path
    segments = []
    current_pos = source_coords
    
    while haversine_km(*current_pos, *dest_coords) > vehicle_range_km:
        # Find nearest station to next waypoint
        nearby_station = find_nearest_station(current_pos, vehicle_range_km)
        segments.append(nearby_station)
        current_pos = (nearby_station["lat"], nearby_station["lng"])
    
    return segments  # List of charging stops
```

---

### 6.7 Value Score Calculation (Compare)

**File**: `backend/routes/compare.py`

```python
# Weighting system for scoring
RANGE_WEIGHT = 0.35      # Range matters most (35%)
PRICE_WEIGHT = 0.30      # Price matters (30%)
BATTERY_WEIGHT = 0.20    # Battery capacity (20%)
RATING_WEIGHT = 0.15     # User rating (15%)

value_score = (
    range_km * RANGE_WEIGHT +
    (1 / price) * PRICE_NORMALIZATION_FACTOR * PRICE_WEIGHT +
    battery_kwh * BATTERY_WEIGHT +
    overall_rating * RATING_WEIGHT
)

# Cost efficiency: How many km per lakh spent
cost_efficiency = range_km / (price / 100_000)
```

---

## 7. Frontend-Backend Connection

### 7.1 API Client Setup

**File**: `frontend/src/services/api.js`

```javascript
import axios from "axios";
import { useAuth } from "../store/useAuth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Add JWT token to headers
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401 & refresh token
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

### 7.2 State Management (Zustand)

**File**: `frontend/src/store/useAuth.js`

```javascript
import { create } from "zustand";

const useAuth = create((set) => ({
  user: null,
  token: localStorage.getItem("auth_token") || null,
  isAuthenticated: !!localStorage.getItem("auth_token"),

  setToken: (token) => {
    localStorage.setItem("auth_token", token);
    set({ token, isAuthenticated: !!token });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.removeItem("auth_token");
    set({ user: null, token: null, isAuthenticated: false });
  },
}));

export default useAuth;
```

---

### 7.3 Query Handling (React Query)

**File**: `frontend/src/pages/BrowsePage.jsx`

```javascript
import { useQuery } from "@tanstack/react-query";
import api from "../services/api";

export default function BrowsePage() {
  const [filters, setFilters] = useState({
    category: "4W",
    brand: null,
    min_price: null,
    max_price: null,
    page: 1,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["vehicles", filters],
    queryFn: () => 
      api.get("/api/vehicles/", { params: filters }).then(r => r.data),
    staleTime: 5 * 60 * 1000,  // Cache for 5 mins
    retry: 1,
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {/* Filter components */}
      {/* Vehicle grid */}
      {data?.vehicles?.map(vehicle => (
        <VehicleCard key={vehicle.id} vehicle={vehicle} />
      ))}
      {/* Pagination */}
    </div>
  );
}
```

---

### 7.4 Real-Time Chat Streaming

**File**: `frontend/src/pages/ChatPage.jsx`

```javascript
async function handleChatSubmit(message) {
  setIsLoading(true);
  
  try {
    // Option 1: Streaming response (Server-Sent Events)
    const response = await fetch(`${API_URL}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    const reader = response.body.getReader();
    let fullResponse = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = new TextDecoder().decode(value);
      fullResponse += chunk;
      
      // Update UI progressively
      setMessages(prev => [...prev, {
        role: "assistant",
        content: fullResponse,
      }]);
    }
  } catch (error) {
    console.error("Chat error:", error);
  } finally {
    setIsLoading(false);
  }
}
```

---

---

## 11. Advanced Features

### RAG Pipeline Capabilities

**1. Query Understanding**
- Intent detection: recommendation, comparison, specification, location, policy, capability
- Multi-language support for Indian languages (aliases in query_parser.py)
- Ambiguity handling with clarification prompts
- Budget parsing: "15 lakh" → 1,500,000 INR
- Range understanding: "under 1.5L" vs "between 15-20L"

**2. Semantic Search**
- FAISS vector index with 384-dimensional embeddings
- Top-K retrieval (default K=3)
- Similarity scoring for relevance ranking
- Optional NVIDIA reranker for production quality

**3. Hybrid Retrieval**
- Combines vector search + structured SQL filtering
- Vehicle type + segment filtering (car vs 3W vs truck)
- Price/range/battery constraints applied
- Commercial vehicle filtering for passenger segments

**4. Session Memory**
- 12-message context window (last 12 messages)
- User expertise level tracking (Beginner, Intermediate, Expert)
- Conversation continuity across multi-turn queries
- Memory fallback: SQLAlchemy + in-memory (_MEMORY_MESSAGES)

**5. Response Generation**
- LLM-powered contextual answers
- Source attribution with vehicle references
- Confidence scoring (grounded vs uncertain)
- Support for streaming (SSE) and buffered responses

### AI Provider Support

The backend supports **4 different LLM providers** (fallback order):

1. **OpenAI** (gpt-4o-mini) - Highest quality, requires API key
2. **Groq** (Llama 3.1 8B) - Fast inference, free tier available
3. **HuggingFace** (Arch-Router 1.5B) - Lightweight, edge deployment
4. **Google Gemini** - Alternative for cost optimization

**Provider Selection** (automatic fallback):
```python
if OPENAI_ENABLED:
    use OpenAI (gpt-4o-mini)
elif GROQ_MODEL_ENABLED:
    use Groq (Llama 3.1)
elif HF_MODEL_ENABLED:
    use HuggingFace (Arch-Router)
else:
    use Gemini (fallback)
```

### Optional Features

**NVIDIA Reranker** (disabled by default)
- Requires: `NVIDIA_API_KEY` + `NVIDIA_RERANK_ENABLED=true`
- Improves ranking of retrieved candidates
- 6-second timeout for performance
- Fallback to local scoring if unavailable

**Knowledge Articles** (20 articles)
- Battery tech explainers
- Charging guides
- Policy overviews
- Buying guides by segment
- Cost calculations
- Maintenance & warranty info

### Out-of-Domain Handling

The system recognizes and blocks queries about:
- Politics, sports, celebrities
- Programming languages & coding
- Stock markets & finance (non-EV)
- Weather & general knowledge

**Response**: "I'm specialized in India's EV market. Ask me about vehicle recommendations, charging, subsidies, or comparisons."

---

## 12. Testing & Quality Assurance

### Test Files (4 Test Modules)

#### **test_ev_rag_pipeline.py** (24 test cases)
Core RAG functionality tests:

**Document Processing Tests**:
- ✅ Excel normalized into VehicleDocument objects
- ✅ Vehicle text builder includes core fields
- ✅ FAISS index returns correct top-K results

**Query Parser Tests**:
- ✅ Intent parsing (recommendation, comparison)
- ✅ Budget range extraction ("₹15-20L")
- ✅ Vehicle type recognition (car, bike, 3W, truck)
- ✅ Price range heuristics (fallback when LLM fails)

**Conversation Tests**:
- ✅ Greeting handling (hello, namaste, etc.) - no random matches
- ✅ Vague queries request clarification ("best EV")
- ✅ Exact model comparison (Ola S1 Pro vs Ather 450X)
- ✅ Model variant handling (doesn't confuse Ather 450S with 450X)
- ✅ Missing model graceful handling (not in dataset)

**Filtering Tests**:
- ✅ Car recommendations exclude 3W/commercial vehicles
- ✅ 3W queries stay in 3W category
- ✅ Budget filtering returns sorted results
- ✅ Multi-turn conversation consistency

#### **test_chat_40.py** (40 real-world queries)
Comprehensive chatbot evaluation:
- Easy: Direct specs (price, range, battery)
- Medium: Comparisons (2-3 vehicles)
- Hard: Consultative (needs reasoning)
- Expert: Knowledge-based (charging tech, policy)
- Adversarial: Misspellings, petrol cars, out-of-dataset

#### **test_chat_memory_and_filters.py**
- Session persistence across messages
- Context window management (12-msg limit)
- User expertise level tracking
- Clarification prompts for ambiguous queries

#### **test_chat_quality.py**
- Answer relevance scoring
- Source accuracy verification
- Hallucination detection
- Response fluency metrics

### Running Tests

```bash
# Run all tests
cd backend
pytest tests/ -v

# Run specific test
pytest tests/test_ev_rag_pipeline.py::EVRAGPipelineTests::test_comparison_locks_to_exact_requested_models -v

# Run with coverage
pytest tests/ --cov=services --cov-report=html
```

---

## 13. Utility Scripts & Tools

### Data Processing Scripts

#### **build_ev_knowledge_base.py**
Builds the FAISS index from Excel data

**What it does**:
1. Load vehicle Excel → VehicleDocument objects
2. Save to JSON (structured format)
3. Generate embeddings (Sentence-Transformers)
4. Build FAISS index (vector store)
5. Save index metadata

**Usage**:
```bash
cd backend
python scripts/build_ev_knowledge_base.py

# Skip embedding rebuild (use existing)
python scripts/build_ev_knowledge_base.py --skip-embeddings
```

**Output Files**:
- `data/processed/vehicles.json` - Structured vehicle data
- `data/processed/knowledge.faiss` - Vector index
- `data/processed/knowledge.meta.json` - Index metadata

#### **import_excel.py**
Programmatic import of vehicle data

**Features**:
- Validates required columns
- Handles missing values
- Generates embeddings
- Inserts to PostgreSQL

#### **seed_manager.py**
Database seeding utilities
- Create test vehicles
- Reset database state
- Generate sample data

### Quality & Evaluation Scripts

#### **evaluate_chatbot.py**
Comprehensive chatbot evaluation suite

**Metrics**:
- Accuracy (correct vehicle matches)
- Relevance (appropriate suggestions)
- Intent classification accuracy
- Answer quality scoring

**Output**: JSON report with scores per category

#### **benchmark_chatbot_100.py**
Performance benchmarking

**Tests**:
- 100 concurrent chat requests
- Latency measurements (p50, p95, p99)
- Memory usage tracking
- Cache effectiveness

#### **simulate_100_chats.py**
Realistic chat load testing
- Simulates real user behavior
- Tests session persistence
- Validates concurrent access
- Stress tests database

#### **watch_data.py**
Real-time data monitoring
- Tracks file changes
- Auto-rebuilds indices
- Validates data integrity
- Logs changes

---

## 14. Knowledge Base & Articles

### 20 Comprehensive Education Articles

**Buying Guides** (4 articles)
- `01_ev_buying_guide_india.md` - General EV buying guide for India
- `12_electric_two_wheeler_buying_guide.md` - 2W segment guide
- `13_electric_car_buying_guide_india.md` - 4W segment guide
- `14_electric_three_wheeler_guide.md` - 3W commercial guide
- `15_commercial_ev_and_electric_truck_guide.md` - Heavy commercial
- `16_ev_bus_overview_india.md` - Public transport vehicles

**Technical Education** (9 articles)
- `02_claimed_range_vs_real_world_range.md` - Range reality
- `03_battery_capacity_and_efficiency.md` - kWh explained
- `04_ac_vs_dc_charging.md` - Charging types comparison
- `05_charging_connectors_and_standards_india.md` - CCS2, Type 2, etc.
- `06_regenerative_braking_explained.md` - Energy recovery
- `07_battery_degradation_and_battery_life.md` - Warranty & longevity
- `17_ev_safety_warranty_and_maintenance.md` - Safety standards

**Infrastructure & Planning** (5 articles)
- `08_home_charging_for_ev_owners_india.md` - Home charging setup
- `09_public_charging_in_india_practical_guide.md` - Network guide
- `19_ev_charging_etiquette_and_trip_planning.md` - Long distance
- `18_how_to_choose_ev_by_use_case.md` - Use case matching

**Policy & Economics** (2 articles)
- `10_total_cost_of_ownership_ev_vs_ice.md` - TCO analysis
- `11_india_ev_subsidies_and_policy_overview.md` - FAME II, state schemes
- `20_common_ev_myths_and_facts.md` - Myth busting

### Knowledge Retrieval in Chat

When user asks about technical topics, the system:
1. Detects knowledge query (charging, battery, subsidy, safety)
2. Retrieves relevant article(s) via vector search
3. Extracts relevant passages
4. Generates answer with citations
5. Provides source links for deeper reading

**Example**:
```
User: "What happens to EV batteries when they degrade?"
→ Retrieves: 07_battery_degradation_and_battery_life.md
→ Extracts: relevant passages about degradation
→ Answer: Formal answer with source attribution
```

---

## 15. Advanced Features (moved section)

### 8.1 Complete User Journey: "New EV Buyer"

```
┌─ HomePage ─────────────────────────────────────────────────┐
│ • Hero section: "Find Your Perfect EV"                     │
│ • Featured diverse vehicles (GET /api/vehicles/featured)   │
│ • Quick stats: "50+ EVs", "5 Segments", "₹5L - ₹1Cr"      │
│ • Call-to-action buttons: Browse, Chat, Recommend         │
└─────────────────────────────┬───────────────────────────────┘
                               │
                    User clicks "Get Recommendation"
                               │
                               ▼
┌─ RecommendPage ────────────────────────────────────────────┐
│ • Wizard form:                                             │
│   1️⃣  Budget: Slider (₹5L - ₹1Cr)                          │
│   2️⃣  Daily Km: Input (10-500 km)                          │
│   3️⃣  Segment: Dropdown (Car, Bike, Scooter, 3W, Truck)   │
│   4️⃣  Priority: Radio (Range, Price, Speed)               │
│                                                            │
│ • POST /api/recommend/                                     │
│   {budget: 750000, daily_km: 50, segment: "car",          │
│    priority: "range"}                                      │
│                                                            │
│ • Response: 30 recommended vehicles sorted by priority    │
│                                                            │
│ • Display: Ranked list with scores                         │
│           Filters: Refine results                          │
│           Actions: "View Details", "Compare"               │
└─────────────────────────────┬───────────────────────────────┘
                               │
                    User clicks "Compare" on 3 vehicles
                               │
                               ▼
┌─ ComparePage ──────────────────────────────────────────────┐
│ • POST /api/compare/ with IDs [12, 25, 38]               │
│ • Response includes: Value scores, cost efficiency        │
│                                                            │
│ • Display:                                                 │
│   ├─ 3-column table with all specs                        │
│   ├─ Highlighted "Best Value" vehicle                     │
│   ├─ Charts: Price vs Range, Rating distribution         │
│   └─ Subsidy calculator (GET /api/subsidies/)             │
│       └─ State dropdown: Select your state                │
│           → Shows FAME II + State subsidy                 │
│           → Final price after discounts                   │
│                                                            │
│ • Action: "Save Comparison to Garage"                     │
│           → Redirects to login if not authenticated        │
│           → POST /api/garage/ with vehicle_ids            │
│           → Saved to user's garage                        │
└─────────────────────────────┬───────────────────────────────┘
                               │
                    User clicks vehicle name
                               │
                               ▼
┌─ VehicleDetailPage ────────────────────────────────────────┐
│ • GET /api/vehicles/{vehicle_id}                           │
│                                                            │
│ • Detailed specs:                                          │
│   • Battery: 75 kWh, 440 km range                          │
│   • Charging: 0-80% in 52 min (DC), 8 hrs (AC)           │
│   • Performance: 150 kW motor, 160 kmh top speed         │
│   • Warranty: 8 years / 1.6M km battery warranty         │
│   • Price: ₹18.75L (with subsidy calculator)             │
│                                                            │
│ • Specs table, spec-sheet PDF download                    │
│ • Related articles (if tagged)                            │
│ • Customer reviews (if integrated)                        │
│                                                            │
│ • Actions:                                                │
│   - Add to comparison                                      │
│   - Save to garage                                         │
│   - Chat about this vehicle                               │
└─────────────────────────────┬───────────────────────────────┘
                               │
                    User clicks "Chat about this"
                               │
                               ▼
┌─ ChatPage ─────────────────────────────────────────────────┐
│ • Context: Last viewed vehicle (Tata Nexon EV)            │
│ • User types: "Is it good for daily commute?"             │
│                                                            │
│ • POST /api/chat/stream                                    │
│   ├─ Query parsing: intent="question"                      │
│   ├─ RAG retrieval: Fetch relevant vehicle docs           │
│   ├─ LLM generation: Context-aware answer                 │
│   └─ Streaming response to UI                              │
│                                                            │
│ • Response:                                                │
│   "Yes, Tata Nexon EV is excellent for daily commute.    │
│    440km range covers ~8-10 days of 50km daily driving.   │
│    Fast charging to 80% in 52 min makes refueling easy."  │
│                                                            │
│ • Feedback: Thumbs up/down for response quality           │
│ • Session history: All messages saved                      │
│ • New chat: Click "+" to start fresh                      │
└─────────────────────────────┬───────────────────────────────┘
                               │
                    User finishes exploration
                               │
                               ▼
┌─ GaragePage (Authenticated) ────────────────────────────────┐
│ • GET /api/garage/                                         │
│ • Display all saved comparisons:                           │
│   - "Nexon vs XUV400 vs Punch EV"                          │
│   - "Budget 15L cars"                                      │
│                                                            │
│ • Each item shows:                                         │
│   - 3 thumbnail images                                     │
│   - "View Comparison" button                              │
│   - "Delete" button                                        │
│                                                            │
│ • Actions:                                                 │
│   - Open saved comparison                                  │
│   - Remove from garage                                     │
│   - Share link (future feature)                            │
└────────────────────────────────────────────────────────────┘
```

---

### 8.2 Workflow: "Find Charging Stations"

```
USER JOURNEY:
┌─ User on ComparePage or VehicleDetailPage
│
│ • Clicks "Charging Info" or "Find Stations" button
│
│ ▼
├─ ChargingMapPage loads
│
│ • GET /api/map/stations?city=null → Returns all 10+ stations
│ • Leaflet map displays charging station markers
│
│ • User workflow:
│   1. Enter starting city: "Bengaluru"
│   2. Enter destination: "Mysore"
│   3. Vehicle range: 300 km (auto-filled from selected car)
│   4. Current battery: 90%
│   5. Reserve: 15% (safety margin)
│
│ • POST /api/map/route-plan
│   {
│     "source": "Bengaluru",
│     "destination": "Mysore",
│     "range_km": 300,
│     "start_soc_percent": 90,
│     "reserve_percent": 15
│   }
│
│ ▼
├─ Backend calculates:
│   • Distance Bangalore→Mysore = 150 km
│   • Available range = 300 * 0.9 - (300 * 0.15) = 225 km
│   • Usable distance < total distance? NO
│   → Direct trip possible, no charging needed
│   → But find nearby stations as reference points
│
│ ▼
└─ Frontend displays:
    • Route on map with green checkmark
    • "No charging stops required"
    • 5 nearest stations displayed for reference
    • ETA, fuel consumption stats
```

---

### 8.3 Admin Workflow: Upload Vehicle Dataset

```
ADMIN-ONLY FLOW:
┌─ AdminPage (requires role="admin")
│
│ • JWT token validation: role == "admin"
│ • If not admin → HTTP 403 Forbidden
│
│ ▼
├─ Admin form:
│   1. Upload Excel file (.xlsx)
│   2. Format required:
│      - Columns: brand, model, category, price, range, battery, etc.
│      - 50+ rows of vehicle data
│
│ • POST /api/admin/upload-dataset (with file)
│   └─ Multipart form-data
│
│ ▼
├─ Backend processing:
│   1. Parse Excel using openpyxl
│   2. Validate each row (required fields check)
│   3. Generate embeddings for each vehicle
│   4. INSERT INTO vehicles table
│   5. Rebuild FAISS indices
│   6. Clear cache
│
│ ▼
└─ Response:
    {
      "success": true,
      "imported_count": 52,
      "skipped_rows": 3,
      "errors": ["Row 12: Missing price", ...]
    }

ADMIN DASHBOARD:
├─ GET /api/admin/stats
│  └─ Response:
│     {
│       "total_vehicles": 52,
│       "chat_sessions": 1234,
│       "average_chat_length": 3.2,
│       "top_searched": ["Nexon EV", "XUV400", ...],
│       "users_count": 543
│     }
│
└─ Display as dashboard charts/cards
```

---

## 9. Database Schema

### 9.1 Core Tables

```sql
-- Users table (Authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    auth_provider VARCHAR(30) DEFAULT 'email',  -- 'email', 'google', etc.
    role VARCHAR(20) DEFAULT 'user',            -- 'user', 'admin'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vehicles table (Core data)
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    segment VARCHAR(20),  -- TWO_WHEELER, THREE_WHEELER, FOUR_WHEELER, TRUCK, BUS
    category VARCHAR(10),
    brand VARCHAR(50),
    model VARCHAR(100),
    approx_price_inr INTEGER,
    range_km INTEGER,
    battery_kwh NUMERIC(6,2),
    top_speed_kmh INTEGER,
    motor_kw NUMERIC(6,2),
    charging_type VARCHAR(20),  -- 'AC', 'DC', 'Both'
    charging_time_ac_hrs NUMERIC(4,1),
    charging_time_dc_min INTEGER,
    overall_rating NUMERIC(3,1),
    fame2_subsidy_inr INTEGER DEFAULT 0,
    state_subsidy_inr INTEGER DEFAULT 0,
    market_status VARCHAR(20) DEFAULT 'Available',
    embedding vector(384),  -- pgvector extension
    image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat sessions (Session management)
CREATE TABLE chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200),
    expertise_level VARCHAR(20) DEFAULT 'Novice',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages (Message history)
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES chat_sessions(id),
    role VARCHAR(20),  -- 'user', 'assistant'
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Saved comparisons (Garage)
CREATE TABLE saved_comparisons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    vehicle_ids VARCHAR(255),  -- Comma-separated IDs: "12,25,38"
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subsidy rules (Policy data)
CREATE TABLE subsidy_rules (
    id SERIAL PRIMARY KEY,
    state VARCHAR(50),
    segment VARCHAR(50),
    subsidy_per_kwh INTEGER,
    max_subsidy INTEGER,
    flat_subsidy INTEGER,
    road_tax_waiver BOOLEAN DEFAULT FALSE
);

-- Chat feedback (Quality metrics)
CREATE TABLE chat_feedback (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    vehicle_id INTEGER REFERENCES vehicles(id),
    rating INTEGER,  -- 1 for helpful, -1 for not helpful
    note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_vehicles_category ON vehicles(category);
CREATE INDEX idx_vehicles_brand ON vehicles(brand);
CREATE INDEX idx_vehicles_price ON vehicles(approx_price_inr);
CREATE INDEX idx_vehicles_range ON vehicles(range_km);
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_saved_comparisons_user ON saved_comparisons(user_id);
CREATE INDEX idx_users_email ON users(email);

-- Vector similarity search
CREATE INDEX ON vehicles USING ivfflat (embedding vector_cosine_ops);
```

---

## 10. Deployment & Setup

### 10.1 Local Development Setup

```bash
# 1. Backend Setup
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values:
# OPENAI_API_KEY=sk-...
# DATABASE_URL=postgresql://user:pass@localhost:5432/ev_compare
# JWT_SECRET=your-secret-key

# Initialize database
python scripts/build_ev_knowledge_base.py

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

---

# 2. Frontend Setup
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env:
# VITE_API_URL=http://localhost:8000

# Start dev server
npm run dev  # Runs on http://localhost:5173
```

### 10.2 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# This starts:
# - PostgreSQL database (port 5432)
# - Backend API (port 8000)
# - Frontend (port 80 via nginx)

# Check container health
docker ps
docker logs <container_id>
```

### 10.3 Production Deployment

**Requirements**:
- PostgreSQL 12+
- Python 3.11+
- Node.js 18+

**Steps**:
1. Deploy PostgreSQL to managed service (AWS RDS, Azure DB, GCP Cloud SQL)
2. Build backend Docker image, push to registry (ECR, ACR, GCR)
3. Deploy backend container with secrets (API keys, JWT secret)
4. Build frontend, deploy to CDN (Vercel, Netlify, AWS CloudFront)
5. Configure CORS for cross-origin requests
6. Set up SSL/TLS certificates (Let's Encrypt)

---

## 📊 System Health Checks

### Startup Validation

```python
# backend/services/startup_sync.py
def ensure_data_ready_on_startup():
    checks = {
        "database_connection": check_db_connectivity(),
        "faiss_index": check_faiss_index_exists(),
        "embeddings_model": check_embeddings_model_loaded(),
        "llm_provider": check_llm_provider_availability(),
    }
    
    if all(checks.values()):
        logger.info("✅ All systems operational")
        return {"status": "ready", "checks": checks}
    else:
        logger.warning("⚠️ Some systems degraded", checks)
        return {"status": "degraded", "checks": checks}
```

---

## 📈 API Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET /api/vehicles ✅ |
| 201 | Created | POST /api/auth/signup ✅ |
| 400 | Bad request | Invalid query params |
| 401 | Unauthorized | Missing JWT token |
| 403 | Forbidden | Non-admin accessing admin route |
| 404 | Not found | Vehicle ID doesn't exist |
| 409 | Conflict | Email already registered |
| 500 | Server error | Database connection failed |

---

## 🔐 Security Best Practices

1. **JWT Tokens**
   - 30-minute expiration
   - Refresh token flow (not yet implemented)
   - Stored in localStorage (consider httpOnly cookie alternative)

2. **Password Security**
   - PBKDF2-SHA256 hashing with salt
   - Minimum 8 characters required
   - Hash compared on login

3. **CORS**
   - Frontend URL whitelisted
   - Credentials enabled for cross-origin requests

4. **Database**
   - parameterized queries (SQLAlchemy ORM)
   - Role-based access control (user vs admin)

5. **API Rate Limiting**
   - ⚠️ TODO: Implement using Redis

6. **Input Validation**
   - Pydantic schemas validate all inputs
   - Query parameters type-checked

---

## 📝 Sample Output Screens

### Screen 1: Browse Page
```
┌─────────────────────────────────────────────────────┐
│ 🔋 EV COMPARE APP          [☰] [👤] [❤️]            │
├─────────────────────────────────────────────────────┤
│ FILTERS                                             │
│ ├─ Category: [4W        ▼]                          │
│ ├─ Brand: [All Brands   ▼]                          │
│ ├─ Price: [₹5L - ₹50L             ⬌]               │
│ ├─ Range: [150km - 500km           ⬌]              │
│ └─ Charging: [All ▼]                                │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ┌──────────────────┐ ┌──────────────────┐           │
│ │  Tata Nexon EV   │ │ Mahindra XUV400  │           │
│ │ ┌──────────────┐ │ │ ┌──────────────┐ │           │
│ │ │   [Image]    │ │ │ │   [Image]    │ │           │
│ │ └──────────────┘ │ │ └──────────────┘ │           │
│ │ ₹18.75L          │ │ ₹12.99L          │           │
│ │ 440 km range     │ │ 456 km range     │           │
│ │ ⭐ 4.5 | [+]     │ │ ⭐ 4.3 | [+]     │           │
│ └──────────────────┘ └──────────────────┘           │
│                                                      │
│         << 1  [2]  3  4  5 >>  (50 total)           │
│         [View Comparison (2 selected)] ↗️           │
└─────────────────────────────────────────────────────┘
```

### Screen 2: Comparison Page
```
┌─────────────────────────────────────────────────────┐
│ 🔋 COMPARE: Tata Nexon EV vs Mahindra XUV400       │
├─────────────────────────────────────────────────────┤
│                                                      │
│           Nexon EV    XUV400    Punch EV             │
│ ─────────────────────────────────────────────────   │
│ Price    ₹18.75L      ₹12.99L   ✨ ₹8.99L           │
│ Range     440 km       456 km     300 km            │
│ Battery   75 kWh       52 kWh     42 kWh            │
│ Charging  52 min(DC)   60 min(DC) 80 min(DC)       │
│ Speed     160 kmh      160 kmh    150 kmh           │
│ Rating    ⭐4.5       ⭐4.3      ⭐4.1             │
│ ─────────────────────────────────────────────────   │
│ Value     245.67       189.54     156.23             │
│ Score     (BEST) 👑                                 │
│                                                      │
│ State: [Karnataka ▼]                                │
│                                                      │
│ After Subsidies:                                    │
│ FAME II:     ₹1,50,000  ₹1,20,000  ₹85,000        │
│ State:       ₹25,000    ₹25,000    ₹15,000        │
│ Final:       ₹17,00,000 ₹11,54,000 ₹7,99,000      │
│                                                      │
│ [📊 Charts] [💾 Save to Garage] [🔄 Back]         │
└─────────────────────────────────────────────────────┘
```

### Screen 3: Chat Page
```
┌─────────────────────────────────────────────────────┐
│ 🔋 AI ASSISTANT                      [🏠] [👤]      │
├──────────────────┬──────────────────────────────────┤
│ Chat History     │  New Chat Session [+]             │
│ ────────────────  ──────────────────────────────────│
│ ✓ Best EV under  │  Arun's Assistant                │
│   15 lakh        │                                   │
│ ✓ Compare Nexon  │  Q: What's the cheapest EV?     │
│   vs XUV400      │                                   │
│ ✓ Charging guide │  🤖: The cheapest EV currently  │
│                  │  available is the Bajaj Chetak   │
│ [Delete]         │  (₹75,000), followed by Ather    │
│ [Share]          │  450X (₹1,40,000). However, if   │
│                  │  you want a 4-wheeler, the       │
│                  │  Punch EV at ₹8.99L is the most  │
│                  │  affordable option.              │
│                  │                                   │
│                  │  Sources: Punch EV, Nexon EV,    │
│                  │  Ather 450X                      │
│                  │  [👍] [👎] [Share]               │
│                  │                                   │
│                  │  Q: Can I charge at home?        │
│                  │                                   │
│                  │  ⏳ Assistant typing...           │
│                  │                                   │
│ ┌────────────────────────────────────────────────┐  │
│ │ Ask me about EVs, charging, costs, etc.   [📤] │  │
│ └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Screen 4: Admin Dashboard
```
┌─────────────────────────────────────────────────────┐
│ 🔧 ADMIN DASHBOARD                   [👨‍💼] [🚪]     │
├─────────────────────────────────────────────────────┤
│ [📤 Upload Dataset] [📊 Statistics] [⚙️ Settings]   │
├─────────────────────────────────────────────────────┤
│                                                      │
│ DATASET UPLOAD                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Select Excel file: [Choose file...     ] [📁] │   │
│ │ Format: brand, model, price, range, battery  │   │
│ │                                              │   │
│ │ [🚀 Upload]  [Clear]                         │   │
│ │                                              │   │
│ │ Last upload: 2 days ago (52 vehicles)        │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ STATISTICS                                          │
│ ┌────────────────────┐ ┌────────────────────┐     │
│ │ Total Vehicles     │ │ Chat Sessions      │     │
│ │      52            │ │      1,234         │     │
│ └────────────────────┘ └────────────────────┘     │
│ ┌────────────────────┐ ┌────────────────────┐     │
│ │ Registered Users   │ │ Avg Messages/Chat  │     │
│ │      543           │ │      3.2           │     │
│ └────────────────────┘ └────────────────────┘     │
│                                                      │
│ TOP SEARCHED VEHICLES                               │
│ 1. Tata Nexon EV................ 156 searches      │
│ 2. Mahindra XUV400............. 142 searches      │
│ 3. Ather 450X.................. 128 searches      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Key Takeaways for Research Paper

### Innovation Points
1. **RAG-Powered AI Assistant** - Combines vector search with LLM for domain-specific recommendations
2. **Multi-Segment Support** - Handles 2W, 3W, 4W, Trucks, and Buses in one platform
3. **Real-Time Subsidy Calculation** - Integrates FAME II + 28 state subsidies
4. **Geospatial Route Optimization** - Plans EV trips with charging stations
5. **Value Scoring Algorithm** - Weighted scoring (Range 35%, Price 30%, Battery 20%, Rating 15%)

### Scalability Considerations
- **Vector Store**: FAISS for O(log n) similarity search
- **Database**: PostgreSQL with pgvector for vector embeddings
- **Caching**: React Query + Optional Redis
- **Load Balancing**: Docker Compose ready for Kubernetes deployment

### Future Enhancements
- Real-time charging network data integration
- User-submitted reviews and ratings
- Integration with dealership inventory
- Mobile app (React Native)
- Predictive analytics for resale value

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue**: "CORS Error when accessing API from frontend"
```
Solution: Ensure backend CORS middleware includes frontend URL
Settings: FRONTEND_URL in backend/.env
```

**Issue**: "FAISS index not found"
```
Solution: Run: python scripts/build_ev_knowledge_base.py
This rebuilds embeddings and creates FAISS indices
```

**Issue**: "Chat response taking too long"
```
Solution: Check LLM provider status
GET /api/chat/provider-status
May fallback to cached responses if provider is slow
```

---

**Document Version**: 1.0  
**Last Updated**: May 2026  
**Status**: Ready for Research Paper & Presentation

