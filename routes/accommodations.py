from .. import crud
from ..models import *
from .deps import get_db
from ..rabbit.client import mq_cl
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException, Request


accommodation_router = APIRouter()


@accommodation_router.get("/")
async def get_all_accommodations(request: Request, session: Session = Depends(get_db)) -> AccommodationsPublic:
    
    print(request.headers)
    statement = select(Accommodation)
    accommodations = session.exec(statement).all()
    
    return AccommodationsPublic(data=accommodations)


@accommodation_router.get("/{id}")
async def get_accommodation_by_id(id: int, session: Session = Depends(get_db)) -> Accommodation:

    accommodation = session.get(Accommodation, id)

    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail="No accommodation found with corresponding id"
        )

    return accommodation


@accommodation_router.post("/", status_code=201)
async def create_accommodation(create_accommodation: CreateAccommodation, session: Session = Depends(get_db)) -> CreateAccommodationPublic:
    existing_accommodation = crud.get_accommodation_by_name(session, create_accommodation.name.strip())

    if existing_accommodation:
        raise HTTPException(
            status_code=400,
            detail=f"Accommdation with name {create_accommodation.name} already exists"
        )
    
    accommodation = crud.create_accommodation(session, create_accommodation)

    return CreateAccommodationPublic(
        id=accommodation.id,
        msg="Accommodation created successfully"
    )


@accommodation_router.patch("/{id}")
async def update_accommodation(id: int, update_accommodation: UpdateAccommodation, session: Session = Depends(get_db)) -> UpdateAccommodationPublic:
    accommodation = session.get(Accommodation, id)

    # if id is invalid, return 404
    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail=f"Accommdation with id {id} does not exist"
        )
    
    existing_accommodation = crud.get_accommodation_by_name(session, update_accommodation.name.strip())

    # if name is duplicate, return 400
    # check if accommodation is being updated with same data; if yes, proceed and if no, return 400
    if existing_accommodation and existing_accommodation.id != id:
        raise HTTPException(
            status_code=400,
            detail=f"Accommdation with name {update_accommodation.name} already exists"
        )
    
    accommodation = crud.update_accommodation(session, accommodation, update_accommodation)

    return UpdateAccommodationPublic(accommodation=accommodation, msg=f"Accommodation {accommodation.name} updated successfully")
    

@accommodation_router.delete("/{id}")
async def delete_accommodation(id: int, session: Session = Depends(get_db)) -> DeleteAccommodationPublic:
    accommodation = session.get(Accommodation, id)

    if not accommodation:
        raise HTTPException(
            status_code=404,
            detail=f"Accommdation with id {id} does not exist"
        )
    
    crud.delete_accommodation(session, accommodation)

    # send a msg to listings api to cascade delete
    await mq_cl.send_message(
        "listings.cascade_delete",
        {
            "accommodation_id": id
        }
    )


    return DeleteAccommodationPublic(msg="Accommodation deleted successfully")
