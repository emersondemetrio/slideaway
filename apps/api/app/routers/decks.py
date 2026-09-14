import difflib
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import owns_or_super_admin, require_user
from app.models import Deck, DeckSeries, Role, User
from app.schemas import DeckCreateRequest, DeckSeriesOut, DeckVersionOut

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("", response_model=DeckSeriesOut)
async def create_deck(
    body: DeckCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
) -> DeckSeriesOut:
    series = DeckSeries(owner_id=user.id, title=body.title)
    db.add(series)
    await db.flush()

    version = Deck(series_id=series.id, version_number=1, source_type=body.source_type, content=body.content)
    db.add(version)
    await db.commit()
    await db.refresh(series, attribute_names=["versions"])
    return series


@router.post("/{series_id}/versions", response_model=DeckVersionOut)
async def create_deck_version(
    series_id: uuid.UUID,
    body: DeckCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
) -> DeckVersionOut:
    series = await db.get(DeckSeries, series_id)
    if series is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck series not found")
    await owns_or_super_admin(series.owner_id, user)

    latest = (
        await db.execute(
            select(Deck).where(Deck.series_id == series_id).order_by(Deck.version_number.desc())
        )
    ).scalars().first()
    next_version = (latest.version_number + 1) if latest else 1

    version = Deck(
        series_id=series_id,
        version_number=next_version,
        source_type=body.source_type,
        content=body.content,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


@router.get("", response_model=list[DeckSeriesOut])
async def list_decks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
) -> list[DeckSeriesOut]:
    stmt = select(DeckSeries).options(selectinload(DeckSeries.versions))
    if user.role != Role.SUPER_ADMIN:
        stmt = stmt.where(DeckSeries.owner_id == user.id)
    return (await db.execute(stmt)).scalars().all()


@router.get("/{series_id}/versions/{from_version}/diff/{to_version}")
async def diff_versions(
    series_id: uuid.UUID,
    from_version: int,
    to_version: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
) -> dict:
    series = await db.get(DeckSeries, series_id)
    if series is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck series not found")
    await owns_or_super_admin(series.owner_id, user)

    versions = {
        v.version_number: v
        for v in (
            await db.execute(select(Deck).where(Deck.series_id == series_id))
        ).scalars()
    }
    a, b = versions.get(from_version), versions.get(to_version)
    if a is None or b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Version not found")

    diff = list(
        difflib.unified_diff(
            a.content.splitlines(),
            b.content.splitlines(),
            fromfile=f"v{from_version}",
            tofile=f"v{to_version}",
            lineterm="",
        )
    )
    return {"diff": diff}
