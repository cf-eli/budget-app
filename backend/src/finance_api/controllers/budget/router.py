"""Budget API router aggregation."""

from litestar import Router

from finance_api.controllers.budget import (
    management,
    master_fund_operations,
    master_fund_queries,
    queries,
)

# Collect all route handlers from submodules
route_handlers = [
    # Management endpoints
    management.create_budget,
    management.add_transaction_to_budget,
    management.copy_budgets_from_previous,
    management.delete_budget,
    # Query endpoints
    queries.get_all_budgets,
    queries.get_budgets_names,
    # Master fund operations (mutations)
    master_fund_operations.combine_fund_to_master,
    master_fund_operations.unlink_fund,
    master_fund_operations.apply_fund_increments_endpoint,
    master_fund_operations.discontinue_master_endpoint,
    master_fund_operations.add_month_to_master_endpoint,
    # Master fund queries
    master_fund_queries.calculate_fund,
    master_fund_queries.get_master_fund_details_endpoint,
    master_fund_queries.get_orphaned_masters_endpoint,
]

budget_router = Router(
    path="/api/v1/budgets",
    route_handlers=route_handlers,
    tags=["Budget"],
)
