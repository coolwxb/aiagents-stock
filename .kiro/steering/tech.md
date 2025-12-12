# Technology Stack

## Backend (Python/FastAPI)
- **Framework**: FastAPI with Pydantic v2 for validation
- **Database**: SQLAlchemy 2.0 with SQLite (default) or MySQL
- **Migrations**: Alembic
- **Task Queue**: Celery with Redis (optional)
- **AI**: DeepSeek API via OpenAI-compatible client
- **Data Sources**: AKShare, Tushare, pywencai
- **Trading**: xtquant (MiniQMT) for quantitative trading
- **Technical Analysis**: ta, pandas, numpy

## Frontend (Vue 2)
- **Framework**: Vue 2.6 with Vue CLI 4
- **UI Library**: Element UI 2.13
- **State Management**: Vuex 3
- **Router**: Vue Router 3
- **HTTP Client**: Axios
- **Styling**: SCSS with Element UI theme

## Common Commands

### Backend
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run tests
pytest
```

### Frontend
```bash
# Install dependencies
cd frontend
npm install

# Run development server (port 9528)
npm run dev

# Build for production
npm run build:prod

# Lint code
npm run lint

# Run tests
npm run test:unit
```

## API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Environment Configuration
Copy `.env.example` to `.env` and configure:
- `DEEPSEEK_API_KEY`: Required for AI analysis
- `TUSHARE_TOKEN`: Optional for additional market data
- `MINIQMT_*`: Optional for quantitative trading
- `EMAIL_*` / `WEBHOOK_*`: Optional for notifications
