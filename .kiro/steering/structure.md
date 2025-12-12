# Project Structure

## Root Layout
```
├── backend/          # FastAPI backend application
├── frontend/         # Vue 2 frontend application
├── sqlite_db/        # SQLite database files (shared)
├── xtquant/          # MiniQMT trading SDK (Windows only)
├── docs/             # Documentation (Chinese)
└── old/              # Legacy Streamlit application (deprecated)
```

## Backend Structure (`backend/app/`)
```
app/
├── main.py           # FastAPI application entry point
├── config.py         # Pydantic settings configuration
├── database.py       # SQLAlchemy engine and session
├── api/
│   ├── v1/           # API v1 endpoints (prefix: /api/v1)
│   │   ├── router.py # Route aggregation
│   │   ├── stock.py  # Stock analysis endpoints
│   │   ├── monitor.py# Smart monitoring endpoints
│   │   └── ...       # Other domain endpoints
│   ├── response.py   # Unified response helpers
│   └── deps.py       # Dependency injection
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic request/response schemas
├── services/         # Business logic layer
├── data/             # Data fetching (market data sources)
├── agents/           # AI agent implementations (DeepSeek)
├── db/               # Database operations (CRUD)
├── tasks/            # Celery background tasks
├── policy/           # Trading strategy implementations
└── utils/            # Helper utilities
```

## Frontend Structure (`frontend/src/`)
```
src/
├── main.js           # Vue application entry
├── App.vue           # Root component
├── api/              # API service modules (axios)
├── views/            # Page components
│   ├── monitor/      # Smart monitoring pages
│   ├── sector/       # Sector strategy pages
│   ├── gs-strategy/  # GS strategy pages
│   └── ...           # Other feature pages
├── components/       # Reusable components
├── router/           # Vue Router configuration
├── store/            # Vuex state management
├── utils/            # Utility functions
│   └── request.js    # Axios instance with interceptors
└── styles/           # Global SCSS styles
```

## Key Conventions
- API routes use Chinese tags for Swagger documentation
- All API responses follow `{code, message, data}` format
- Frontend proxies `/dev-api` to backend at `http://127.0.0.1:8000`
- Database files stored in `sqlite_db/` directory at project root
- Environment variables loaded from `.env` file
