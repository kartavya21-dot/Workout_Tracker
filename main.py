from fastapi import FastAPI, Depends, HTTPException, Query
from contextlib import asynccontextmanager
from typing import Annotated, List
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship, JSON, Column
from datetime import datetime

# Day
class DayBase(SQLModel):
    name: str

class Day(DayBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    exercises: List["Exercise"] | None = Relationship(back_populates="day")
    created_at: datetime | None = Field(default_factory=lambda: datetime.now())

class DayCreate(DayBase):
    pass

class DayPublic(DayBase):
    id: int
    created_at: datetime
    exercise: List["ExercisePublicWithDay"]

class DayUpdate(SQLModel):
    name: str | None = None
    exercise: List["Exercise"] | None = None
    created_at: datetime | None = None

# Exercise
class ExerciseBase(SQLModel):
    name: str

class Exercise(ExerciseBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    day_id: int = Field(foreign_key="day.id")
    day: Day = Relationship(back_populates="exercises")
    
    sets: List["Set"] | None = Relationship(back_populates="exercise")

class ExerciseCreate(ExerciseBase):
    day_id: int

class ExercisePublic(ExerciseBase):
    id: int
    day_id: int

class ExerciseUpdate(SQLModel):
    name: str | None = None
    day: int | None = None
    sets: List["Set"] | None = None

class ExercisePublicWithDay(ExerciseBase):
    sets: List["SetPublicWithExercise"]

# Set
class Set(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True) 
    reps: List[int] | None = Field(sa_column=Column(JSON))
    exercise_id: int | None = Field(foreign_key="exercise.id")
    exercise: Exercise = Relationship(back_populates="sets")

class SetUpdate(SQLModel):
    reps: List[int]
    exercise_id: int

class SetPublic(SQLModel):
    id: int
    reps: List[int]
    exercise_id: int

class SetPublicWithExercise(SQLModel):
    reps: List[int]


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session    

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/day")
def get_day(session: SessionDep) -> DayPublic:
    day = session.exec(select(Day)).all()
    return day

@app.get("/exercise")
def get_exercise(session: SessionDep) -> ExercisePublicWithDay:
    exercise = session.exec(select(Exercise)).all()
    return exercise

@app.post("/day")
def create_day(session: SessionDep, day: DayCreate):
    db_day = Day.model_validate(day)
    session.add(db_day)
    session.commit()
    session.refresh(db_day)
    return db_day