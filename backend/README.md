poetry env use $(pyenv which python3.12)



docker run --name postgres_ffxiv --network test_network -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=ffxiv -p 5432:5432 postgres


docker run --rm --network test_network -v $(pwd)/src/toolbox_api/migrations:/flyway/sql flyway/flyway -url=jdbc:postgresql://postgres_ffxiv:5432/ffxiv -user=admin -password=admin -locations=filesystem:/flyway/sql migrate


## Installation

```bash
# Install package
uv sync
```

## Database migrations 

```bash
uv run alembic revision --autogenerate -m "initial migration"

uv run alembic upgrade head
```