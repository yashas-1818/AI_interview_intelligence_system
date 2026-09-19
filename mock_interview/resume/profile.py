from typing import List, Dict
from pydantic import BaseModel, Field


class CandidateInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""


class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    duration: str = ""
    score: str = ""


class Experience(BaseModel):
    company: str = ""
    position: str = ""
    duration: str = ""
    description: str = ""


class Project(BaseModel):
    name: str = ""
    technologies: List[str] = Field(default_factory=list)
    description: str = ""


class CandidateProfile(BaseModel):
    candidate: CandidateInfo = Field(default_factory=CandidateInfo)

    summary: str = ""

    skills: Dict[str, List[str]] = Field(default_factory=dict)

    experience: List[Experience] = Field(default_factory=list)

    projects: List[Project] = Field(default_factory=list)

    leadership: List[str] = Field(default_factory=list)

    certifications: List[str] = Field(default_factory=list)

    education: List[Education] = Field(default_factory=list)