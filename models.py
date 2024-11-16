from typing import Optional
from .core.config import config
from sqlmodel import Field, SQLModel


# base model for all models
# makes sure that all models are created in the appropriate schema
class BaseModel(SQLModel):
    __table_args__ = {"schema": str(config.DB_SCHEMA)}


# request models
# todo: add rule to strip and check empty strings https://stackoverflow.com/a/70262769/10513667
# todo: add a base model for inheriting common fields


class CreateAccommodation(BaseModel):
    name: str = Field(unique=True)
    country: str
    city: str
    address: str
    postcode: str
    

class UpdateAccommodation(BaseModel):
    name: str | None = Field(unique=True)
    country: str | None
    city: str | None
    address: str | None
    postcode: str | None


# db models

class Accommodation(BaseModel, table=True):
    id: int | None = Field(primary_key=True, default=None) # make sure to have a default=none to avoid Accomodation.model_validate() failing
    name: str = Field(unique=True)
    country: str
    city: str
    address: str
    postcode: str


# response models 

class AccommodationsPublic(BaseModel):
    data: list[Accommodation]


class CreateAccommodationPublic(BaseModel):
    id: int
    msg: str


class UpdateAccommodationPublic(BaseModel):
    accommodation: Accommodation
    msg: str


class DeleteAccommodationPublic(BaseModel):
    msg: str