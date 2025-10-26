## Starting the backend Server

### 1. CD into Backend Directory

```bash
cd backend
```

### 2. Set Up Python Environment

```bash
uv sync
```

### 3. Set Up PostgreSQL Database
```bash
docker run --name db -e POSTGRES_DB=finance -e POSTGRES_PASSWORD=postgres -d postgres -p 5432
```

### 4. Configure Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DB='localhost'
DB_PORT='5432'
DB_USER='postgres'
DB_PASSWORD='postgres'
FINANCE_DB_NAME='finance'

# Authentication (optional)
ENABLE_AUTH='false'
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start the Development Server

```bash
# Run the API server
uv run uvicorn asgi:app --reload --port 8082 --log-level debug
```

The API will be available at `http://localhost:8082/`

### 7. Access API Documentation

Once running, visit:
- **OpenAPI Specs**: `http://localhost:8082/openapi.json`
- **Redoc**: `http://localhost:8082/redoc`
- **Swagger UI**: `http://localhost:8082/docs`