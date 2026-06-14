from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

# User Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field("seeker", description="seeker, employer, or admin")

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# Seeker Profile Schemas
class SeekerProfileCreate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    resume_url: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None

class SeekerProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    resume_url: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None

class SeekerProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    bio: Optional[str] = None
    resume_url: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponseWithProfile(UserResponse):
    seeker_profile: Optional[SeekerProfileResponse] = None

# Job Listing Schemas
class JobListingCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10)
    requirements: str = Field(..., min_length=5)
    location: str = Field(..., min_length=2, max_length=100)
    job_type: str = Field(..., description="Full-time | Part-time | Internship | Remote")
    salary_range: Optional[str] = None

class JobListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    is_active: Optional[bool] = None

class JobListingResponse(BaseModel):
    id: int
    employer_id: int
    title: str
    description: str
    requirements: str
    location: str
    job_type: str
    salary_range: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Application Schemas
class ApplicationCreate(BaseModel):
    cover_letter: Optional[str] = None

class ApplicationUpdateStatus(BaseModel):
    status: str = Field(..., description="applied | interviewing | accepted | rejected")

class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    seeker_id: int
    resume_url: str
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    job: Optional[JobListingResponse] = None

    class Config:
        from_attributes = True
