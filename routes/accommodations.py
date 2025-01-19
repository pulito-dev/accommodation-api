from .. import crud
from ..models import *
from sqlmodel import  select
from ..rabbit.client import mq_cl
from .deps import get_session, get_current_user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession


accommodation_router = APIRouter()


@accommodation_router.get("/")
async def get_all_accommodations(session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)) -> AccommodationsPublic:
    
    statement = select(Accommodation)
    res = await session.execute(statement)
    accommodations = res.scalars().all()

    return AccommodationsPublic(data=accommodations)


@accommodation_router.get("/my")
async def get_user_accommodations(session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)) -> AccommodationsPublic:
    
    accommodations = await crud.get_user_accommodations(session, current_user.get("id"))

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
async def create_accommodation(
    create_accommodation: CreateAccommodation,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
    ) -> CreateAccommodationPublic:

    existing_accommodation = await crud.get_accommodation_by_name(session, create_accommodation.name.strip())

    if existing_accommodation:
        raise HTTPException(
            status_code=400,
            detail=f"Accommdation with name {create_accommodation.name} already exists"
        )
    
    # inject user id from the current_user
    create_accommodation = CreateAccommodationFull(
        name=create_accommodation.name,
        country=create_accommodation.country,
        city=create_accommodation.city,
        address=create_accommodation.address,
        postcode=create_accommodation.postcode,
        user_id=current_user.get("id")
    )
    
    accommodation = await crud.create_accommodation(session, create_accommodation)

    return CreateAccommodationPublic(
        id=accommodation.id,
        msg="Accommodation created successfully"
    )


@accommodation_router.patch("/{id}")
async def update_accommodation(id: int, update_accommodation: UpdateAccommodation, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)) -> UpdateAccommodationPublic:
    accommodation = await session.get(Accommodation, id)

    # if id is invalid, return 404
    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail=f"Accommdation with id {id} does not exist"
        )
    
    # check if the user is trying to update his own accommodation
    if accommodation.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You cannot delete this accommodation"
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
async def delete_accommodation(id: int, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)) -> DeleteAccommodationPublic:
    accommodation = await session.get(Accommodation, id)

    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail=f"Accommdation with id {id} does not exist"
        )
    
    # check if the user is trying to delete his own accommodation
    if accommodation.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You cannot delete this accommodation"
        )
    
    session.begin()
    try:
        await crud.delete_accommodation(session, accommodation)
        
        # send a msg to listings api to cascade delete
        res = await mq_cl.send_rpc_message(
            "listings.cascade_delete",
            {
                "accommodation_id": id
            }
        )

        if not res.get("success"):
            raise Exception()
    except:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=res.get("msg", "Something went wrong")
        )
    else:
        await session.commit()
        return DeleteAccommodationPublic(msg="Accommodation deleted successfully")
