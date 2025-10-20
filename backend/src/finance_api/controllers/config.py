from finance_api.config import settings

db_config = {
    "dbname": settings.db_name,
    "user": settings.db_user,
    "password": settings.db_password,
    "host": settings.db_host,
    "port": settings.db_port,
    "PLAID_ENVIRONMENT": settings.plaid_environment,
    "PLAID_CLIENT_ID": settings.plaid_client_id,
    "PLAID_SECRET": settings.plaid_secret,
}
