from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MatchProfileExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: Optional[bool] = None


class MatchProfileEducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None


class MatchProfile(BaseModel):
    full_name: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[MatchProfileExperienceItem] = Field(default_factory=list)
    education: List[MatchProfileEducationItem] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class MatchJob(BaseModel):
    id: Optional[str] = None
    title: str
    company: Optional[str] = None
    description: str
    requirements: List[str] = Field(default_factory=list)
    nice_to_have: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None
    location: Optional[str] = None


class MatchPreviewRequest(BaseModel):
    profile: MatchProfile
    job: MatchJob


class MatchDetailScores(BaseModel):
    skills_score: int
    experience_score: int
    semantic_score: int


class MatchPreviewResponse(BaseModel):
    score: int
    summary: str
    strengths: List[str]
    gaps: List[str]
    suggestions: List[str]
    details: MatchDetailScores
    debug: Optional[Dict[str, Any]] = None


class MatchBatchRequest(BaseModel):
    profile: MatchProfile
    jobs: List[MatchJob] = Field(default_factory=list)


class MatchBatchItemResponse(BaseModel):
    job_id: Optional[str] = None
    score: int
    summary: str
    strengths: List[str]
    gaps: List[str]
    suggestions: List[str]
    details: MatchDetailScores


class MatchBatchResponse(BaseModel):
    items: List[MatchBatchItemResponse] = Field(default_factory=list)