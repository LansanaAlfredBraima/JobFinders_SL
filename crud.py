from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
import models
import schemas
from auth import get_password_hash

# --- User CRUD ---
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    """Retrieve a user by their username."""
    query = select(models.User).where(models.User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    """Retrieve a user by their email address."""
    query = select(models.User).where(models.User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    """Create a new user. If seeker, automatically initialize an empty seeker profile."""
    hashed_pw = get_password_hash(user_in.password)
    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw,
        role=user_in.role
    )
    db.add(db_user)
    await db.flush()  # Populates user id

    if db_user.role == "seeker":
        db_profile = models.SeekerProfile(user_id=db_user.id)
        db.add(db_profile)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- Profile CRUD ---
async def get_profile_by_user_id(db: AsyncSession, user_id: int) -> Optional[models.SeekerProfile]:
    """Retrieve a seeker profile by user ID."""
    query = select(models.SeekerProfile).where(models.SeekerProfile.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_profile(
    db: AsyncSession,
    profile: models.SeekerProfile,
    profile_in: schemas.SeekerProfileUpdate
) -> models.SeekerProfile:
    """Update profile fields with provided values."""
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile

# --- Job Listing CRUD ---
async def create_job_listing(
    db: AsyncSession,
    job_in: schemas.JobListingCreate,
    employer_id: int
) -> models.JobListing:
    """Create a new job opportunity listing."""
    db_job = models.JobListing(
        employer_id=employer_id,
        title=job_in.title,
        description=job_in.description,
        requirements=job_in.requirements,
        location=job_in.location,
        job_type=job_in.job_type,
        salary_range=job_in.salary_range,
        is_active=True
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job

async def get_job_listing(db: AsyncSession, job_id: int) -> Optional[models.JobListing]:
    """Retrieve a specific job listing by ID."""
    query = select(models.JobListing).where(models.JobListing.id == job_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_job_listings(
    db: AsyncSession,
    keyword: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> List[models.JobListing]:
    """Retrieve a list of active job listings filterable by title/desc, location, and job type."""
    query = select(models.JobListing).where(models.JobListing.is_active == True)
    
    filters = []
    if keyword:
        filters.append(
            or_(
                models.JobListing.title.ilike(f"%{keyword}%"),
                models.JobListing.description.ilike(f"%{keyword}%")
            )
        )
    if location:
        filters.append(models.JobListing.location.ilike(f"%{location}%"))
    if job_type:
        filters.append(models.JobListing.job_type.ilike(f"%{job_type}%"))
        
    if filters:
        query = query.where(and_(*filters))
        
    query = query.order_by(models.JobListing.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_job_listing(
    db: AsyncSession,
    job: models.JobListing,
    job_in: schemas.JobListingUpdate
) -> models.JobListing:
    """Update job listing details."""
    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
        
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

async def delete_job_listing(db: AsyncSession, job: models.JobListing) -> None:
    """Delete a job listing from the database."""
    await db.delete(job)
    await db.commit()

# --- Application CRUD ---
async def create_application(
    db: AsyncSession,
    job_id: int,
    seeker_id: int,
    resume_url: str,
    cover_letter: Optional[str] = None
) -> models.Application:
    """Submit a job application for a seeker."""
    db_app = models.Application(
        job_id=job_id,
        seeker_id=seeker_id,
        resume_url=resume_url,
        cover_letter=cover_letter,
        status="applied"
    )
    db.add(db_app)
    await db.commit()
    # Fetch with selectinload to ensure the 'job' relationship is fully preloaded for Pydantic serialization
    query = select(models.Application).where(models.Application.id == db_app.id).options(selectinload(models.Application.job))
    result = await db.execute(query)
    return result.scalar_one()

async def get_application(db: AsyncSession, app_id: int) -> Optional[models.Application]:
    """Retrieve an application by ID."""
    query = select(models.Application).where(models.Application.id == app_id).options(selectinload(models.Application.job))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_applications_for_seeker(db: AsyncSession, seeker_id: int) -> List[models.Application]:
    """Retrieve all applications submitted by a specific seeker, including job details."""
    query = select(models.Application).where(models.Application.seeker_id == seeker_id).options(selectinload(models.Application.job)).order_by(models.Application.applied_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_applications_for_employer_jobs(db: AsyncSession, employer_id: int) -> List[models.Application]:
    """Retrieve all applications submitted for jobs owned by a specific employer, including job details."""
    query = (
        select(models.Application)
        .join(models.JobListing, models.Application.job_id == models.JobListing.id)
        .where(models.JobListing.employer_id == employer_id)
        .options(selectinload(models.Application.job))
        .order_by(models.Application.applied_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_application_status(
    db: AsyncSession,
    application: models.Application,
    status: str
) -> models.Application:
    """Update status of a job application."""
    application.status = status
    db.add(application)
    await db.commit()
    # Fetch with selectinload to ensure the 'job' relationship is fully preloaded for Pydantic serialization
    query = select(models.Application).where(models.Application.id == application.id).options(selectinload(models.Application.job))
    result = await db.execute(query)
    return result.scalar_one()
