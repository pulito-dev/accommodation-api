from .models import *
from sqlmodel import Session, select


def get_accommodation_by_name(session: Session, name: str) -> Accommodation | None:
    statement = select(Accommodation).where(Accommodation.name == name)
    accommodation = session.exec(statement).first()

    return accommodation


def create_accommodation(session: Session, accommodation_create: CreateAccommodation) -> Accommodation:
    accommodation = Accommodation.model_validate(
        accommodation_create
    )
    session.add(accommodation)
    session.commit()
    session.refresh(accommodation)

    return accommodation


def update_accommodation(session: Session, db_accommodation: Accommodation, accommodation_update: UpdateAccommodation) -> Accommodation:
    new_data = accommodation_update.model_dump(
        # FIXME: not working
        # https://stackoverflow.com/questions/72606747/sqlmodel-behaves-differently-from-pydantic-basemodel-in-exclude-unset
        exclude_unset=True,
        )    
    db_accommodation.sqlmodel_update(
        new_data
    )
    session.add(db_accommodation)
    session.commit()
    session.refresh(db_accommodation)

    return db_accommodation


def delete_accommodation(session: Session, db_accommodation: Accommodation):
    session.delete(db_accommodation)
    session.commit()
