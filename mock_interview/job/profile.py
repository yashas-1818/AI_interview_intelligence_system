from typing import List
from pydantic import BaseModel, Field


class JobProfile(BaseModel):
    """
    Structured representation of a target job/role.
    """

    role_title: str = ""

    company: str = ""

    summary: str = ""

    required_skills: List[str] = Field(
        default_factory=list
    )

    preferred_skills: List[str] = Field(
        default_factory=list
    )

    responsibilities: List[str] = Field(
        default_factory=list
    )

    qualifications: List[str] = Field(
        default_factory=list
    )

    experience_required: str = ""

    education_required: List[str] = Field(
        default_factory=list
    )

    tools_and_technologies: List[str] = Field(
        default_factory=list
    )

    keywords: List[str] = Field(
        default_factory=list
    )