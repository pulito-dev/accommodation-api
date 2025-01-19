from .models import *
from sqlmodel import select
from sqlalchemy.ext.asyncio.session import AsyncSession


async def get_accommodation_by_name(session: AsyncSession, name: str) -> Accommodation | None:
    statement = select(Accommodation).where(Accommodation.name == name)
    res = await session.execute(statement)

    accommodation = res.scalars().first()

    return accommodation


async def get_user_accommodations(session: AsyncSession, user_id: int) -> list[Accommodation]:
    statement = select(Accommodation).where(Accommodation.user_id == user_id)
    
    res = await session.execute(statement)

    accommodations = res.scalars().all()

    return accommodations


async def create_accommodation(session: AsyncSession, accommodation_create: CreateAccommodationFull) -> Accommodation:
    accommodation = Accommodation.model_validate(
        accommodation_create
    )
    session.add(accommodation)
    await session.commit()
    await session.refresh(accommodation)

    return accommodation


async def update_accommodation(session: AsyncSession, db_accommodation: Accommodation, accommodation_update: UpdateAccommodation) -> Accommodation:
    new_data = accommodation_update.model_dump(
        exclude_unset=True,
        )
    db_accommodation.sqlmodel_update(
        new_data
    )
    session.add(db_accommodation)
    session.commit()
    session.refresh(db_accommodation)

    return db_accommodation


async def delete_accommodation(session: AsyncSession, db_accommodation: Accommodation):
    await session.delete(db_accommodation)
