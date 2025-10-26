"""Save SimpleFin data to PostgreSQL using SQLAlchemy Core."""

import logging
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.db import get_session
from finance_api.models.organization import SimpleFinOrganization
from finance_api.schemas.schema import Organization

LOGGER = logging.getLogger(__name__)


async def save_organization(
    org: Organization,
    session: AsyncSession | None = None,
) -> None:
    """
    Save or update organization using upsert.

    NOTE: This currently does nothing if the org already exists.
    To enable updating, uncomment the on_conflict_do_update section.

    Args:
        org: Organization object
        session: Optional database session. If None, creates a new session.

    """
    async with get_session(session) as sess:
        stmt = insert(SimpleFinOrganization).values(
            domain=org.domain,
            name=org.name or "",
            sfin_url=org.sfin_url,
            url=org.url or "",
            org_id=org.id or "",
            updated_at=datetime.now(UTC),
        )
        stmt = stmt.on_conflict_do_nothing()
        await sess.execute(stmt)
        await sess.commit()
        LOGGER.debug("Saved organization: %s", org.name or org.domain)
