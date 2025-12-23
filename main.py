from fastapi import FastAPI, Depends, HTTPException, Query
from contextlib import asynccontextmanager
from typing import Annotated, List, Optional
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
    id: int | None
    created_at: datetime | None
    exercises: List["ExercisePublicWithDay"] | None = []

class DayUpdate(SQLModel):
    name: str | None = None
    exercises: List["Exercise"] | None = None
    created_at: datetime | None = None

# Exercise
class ExerciseBase(SQLModel):
    name: str

class Exercise(ExerciseBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    day_id: int | None = Field(foreign_key="day.id")
    day: Day | None = Relationship(back_populates="exercises")

    sets: List["Set"] | None = Relationship(back_populates="exercise")

class ExerciseCreate(ExerciseBase):
    day_id: int

class ExercisePublic(ExerciseBase):
    id: int | None
    day_id: int | None

class ExerciseUpdate(SQLModel):
    name: str | None = None
    day_id: int | None = None
    sets: List["Set"] | None = None

class ExercisePublicWithDay(ExerciseBase):
    sets: List["SetPublic"]

# Set
class SetBase(SQLModel):
    unit: str
    count: int

class Set(SetBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    exercise_id: int | None = Field(foreign_key="exercise.id")
    exercise: Exercise = Relationship(back_populates="sets")

class SetCreate(SetBase):
    exercise_id: int

class SetPublic(SetBase):
    id: int
    exercise_id: int

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

@app.get("/day", response_model=List[DayPublic])
def get_day(
    session: SessionDep,
    date_start: Optional[datetime] = Query(
        default=None,
        description="Filter days created after this date"
    ),
    date_end: Optional[datetime] = Query(
        default=None,
        description="Filter days created before this date"
    )
):
    statement = select(Day)

    if date_start:
        statement = statement.where(Day.created_at >= date_start)

    if date_end:
        statement = statement.where(Day.created_at <= date_end)

    days = session.exec(statement).all()
    return days

@app.post("/day", response_model=DayPublic)
def create_day(session: SessionDep, day: DayCreate):
    db_day = Day.model_validate(day)
    session.add(db_day)
    session.commit()
    session.refresh(db_day)
    return db_day

@app.get("/exercise", response_model=List[ExercisePublicWithDay])
def get_exercise(session: SessionDep):
    exercise = session.exec(select(Exercise)).all()
    return exercise

@app.post("/addExerciseToDay")
def create_exercise(session: SessionDep, exercise: ExerciseCreate):
    db_exercise = Exercise.model_validate(exercise)
    session.add(db_exercise)
    session.commit()
    session.refresh(db_exercise)
    return db_exercise

@app.post("/addSetToExercise", response_model= SetPublic)
def create_set(session: SessionDep, set: SetCreate):
    db_set = Set.model_validate(set)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    return db_set

@app.post("/addSetInBulk", response_model=List[SetPublic])
def create_set_in_bulk(session: SessionDep, sets: List[SetCreate]):

    db_sets = [Set.model_validate(s) for s in sets]

    session.add_all(db_sets)
    session.commit()

    for set in db_sets:
        session.refresh(set)

    return db_sets