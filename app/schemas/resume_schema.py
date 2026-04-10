from pydantic import BaseModel
from typing import List, Optional


class ExperienceItem(BaseModel):
    company: str
    role: str
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None


class EducationItem(BaseModel):
    institution: str
    degree: str
    year: Optional[str] = None


class ResumeStructuredData(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    experiences: List[ExperienceItem] = []
    education: List[EducationItem] = []