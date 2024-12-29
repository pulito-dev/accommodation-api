from .. import crud
from ..models import *
from sqlmodel import  select
from .deps import get_session
from ..rabbit.client import mq_cl
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession


accommodation_router = APIRouter()


@accommodation_router.get("/")
async def get_all_accommodations(session: AsyncSession = Depends(get_session)) -> AccommodationsPublic:
    
    statement = select(Accommodation)
    res = await session.execute(statement)
    accommodations = res.scalars().all()
    
    return AccommodationsPublic(data=accommodations)


@accommodation_router.get("/{id}")
async def get_accommodation_by_id(id: int, session: AsyncSession = Depends(get_session)) -> Accommodation:

    accommodation = await session.get(Accommodation, id)

    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail="No accommodation found with corresponding id"
        )

    return accommodation


@accommodation_router.post("/", status_code=201)
async def create_accommodation(create_accommodation: CreateAccommodation, session: AsyncSession = Depends(get_session)) -> CreateAccommodationPublic:
    existing_accommodation = await crud.get_accommodation_by_name(session, create_accommodation.name.strip())

    if existing_accommodation:
        raise HTTPException(
            status_code=400,
            detail=f"Accommdation with name {create_accommodation.name} already exists"
        )
    
    accommodation = await crud.create_accommodation(session, create_accommodation)

    return CreateAccommodationPublic(
        id=accommodation.id,
        msg="Accommodation created successfully"
    )


@accommodation_router.patch("/{id}")
async def update_accommodation(id: int, update_accommodation: UpdateAccommodation, session: AsyncSession = Depends(get_session)) -> UpdateAccommodationPublic:
    accommodation = await session.get(Accommodation, id)

    # if id is invalid, return 404
    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail=f"Accommdation with id {id} does not exist"
        )
    
    existing_accommodation = await crud.get_accommodation_by_name(session, update_accommodation.name.strip())

    # if name is duplicate, return 400
    # check if accommodation is being updated with same data; if yes, proceed and if no, return 400
    if existing_accommodation and existing_accommodation.id != id:
        raise HTTPException(
            status_code=400,
            detail=f"Accommdation with name {update_accommodation.name} already exists"
        )
    
    accommodation = await crud.update_accommodation(session, accommodation, update_accommodation)

    return UpdateAccommodationPublic(accommodation=accommodation, msg=f"Accommodation {accommodation.name} updated successfully")
    

@accommodation_router.delete("/{id}")
async def delete_accommodation(id: int, session: AsyncSession = Depends(get_session)) -> DeleteAccommodationPublic:
    accommodation = await session.get(Accommodation, id)

    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail=f"Accommdation with id {id} does not exist"
        )
    
    await crud.delete_accommodation(session, accommodation)

    # send a msg to listings api to cascade delete
    await mq_cl.send_message(
        "listings.cascade_delete",
        {
            "accommodation_id": id
        }
    )


    return DeleteAccommodationPublic(msg="Accommodation deleted successfully")
