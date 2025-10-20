from sqlalchemy import insert, select
from finance_api.schemas.schema import FinancialData, Organization, Account, Transaction
from finance_api.models.db import engine

"""Save SimpleFin data to PostgreSQL using SQLAlchemy Core."""
from sqlalchemy import (
    create_engine, 
    Table, 
    Column, 
    String, 
    DateTime, 
    Boolean, 
    Float,
    ForeignKey,
    MetaData,
    Integer,
    Text,
    # insert,
    select,
    update,
    and_
)
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone
from typing import List
import logging
from finance_api.models.organization import SimpleFinOrganization
from sqlalchemy.ext.asyncio import AsyncSession

LOGGER = logging.getLogger(__name__)


async def save_organization(org: Organization) -> None:
    """Save or update organization using upsert.

    NOTE: This currently does nothing if the org already exists.
    To enable updating, uncomment the on_conflict_do_update section.
    
    Args:
        org: Organization object
    """
    stmt = insert(SimpleFinOrganization).values(
        domain=org.domain,
        name=org.name or '',
        sfin_url=org.sfin_url,
        url=org.url or '',
        org_id=org.id or '',
        updated_at=datetime.now(timezone.utc)
    )
    
    stmt = stmt.on_conflict_do_nothing()

    # Upsert: update if exists
    # stmt = stmt.on_conflict_do_update(
    #     index_elements=['domain'],
    #     set_={
    #         'sfin_url': stmt.excluded.sfin_url,
    #         'url': stmt.excluded.url,
    #         'name': stmt.excluded.name,
    #         'updated_at': datetime.now(datetime.timezone.utc)
    #     }
    # )
    async with AsyncSession(engine) as session:
        await session.execute(stmt)
        await session.commit()
    LOGGER.debug(f"Saved organization: {org.name or org.domain}")
