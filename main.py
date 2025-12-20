from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from datetime import date

app = FastAPI()

class Day(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: date | None
    exercises: list["Exercise"] = Relationship(back_populates="team")
    name: str

class Exercise(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    day: str | None = Field(default=None, foreign_key="team.id")
    sets: list["Set"] = Relationship(back_populates="exercise")

class Set(SQLModel):
    id: int | None = Field(default=None, primary_key=True) 
    reps: list[int]
    exercise: list["Exercise"] = Relationship(back_populates="sets")
