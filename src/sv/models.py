"""Typed records shared by every pipeline step."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ItemType = Literal["lecture", "reading", "quiz", "assignment", "discussion",
                   "resource", "lab", "other"]


# --- Course manifest ---------------------------------------------------------

class ManifestItem(BaseModel):
    n: int
    item_id: str
    type: ItemType
    coursera_kind: str            # Coursera's own type name, kept for the adapter
    title: str
    slug: str
    public_url: str
    access_url: str
    duration_s: int | None = None
    skip_reason: str | None = None


class Lesson(BaseModel):
    n: int
    title: str
    items: list[ManifestItem] = []


class Module(BaseModel):
    n: int
    id: str
    title: str
    objectives: list[str] = []
    lessons: list[Lesson] = []


class CourseManifest(BaseModel):
    course_key: str               # short alias, e.g. gpm1
    slug: str
    course_id: str
    title: str
    program: dict[str, str] = {}
    modules: list[Module] = []
    discovered_at: datetime


# --- Normalized item -----------------------------------------------------------

class Cue(BaseModel):
    i: int
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    source: Literal["coursera-manual", "coursera-auto", "whisper"]
    lang: str = "en"
    cues: list[Cue]


class Paragraph(BaseModel):
    pid: str                      # p1..pn
    md: str


class QuizQuestion(BaseModel):
    qid: str
    stem: str
    options: list[str] = []
    my_answer: list[int] | str | None = None
    correct: list[int] | str | None = None
    correct_source: Literal["shown", "inferred-from-graded", "unknown"] = "unknown"
    feedback: str | None = None


class Asset(BaseModel):
    kind: Literal["image", "pdf", "xlsx", "docx", "pptx", "frame", "contact-sheet", "other"]
    path: str                     # relative to the data root
    sha256: str
    caption: str | None = None


class NormItem(BaseModel):
    id: str                       # <course_key>.<item_id>
    type: ItemType
    order: str                    # "MM.LL.II"
    title: str
    url: str
    duration_s: int | None = None
    transcript: Transcript | None = None
    paragraphs: list[Paragraph] = []
    questions: list[QuizQuestion] = []
    assets: list[Asset] = []
    fetched_at: datetime
    raw_sha256: str
    flags: list[str] = []


# --- State manifest ------------------------------------------------------------

class StepState(BaseModel):
    at: datetime | None = None
    sha256: str | None = None     # hash of this step's output
    input_sha256: str | None = None
    detail: dict = Field(default_factory=dict)


class ItemState(BaseModel):
    fetched: StepState = Field(default_factory=StepState)
    normalized: StepState = Field(default_factory=StepState)
    generated: StepState = Field(default_factory=StepState)
    validated: StepState = Field(default_factory=StepState)
    history: list[dict] = []
