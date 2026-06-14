from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from database import get_db
import crud
import schemas
import auth
import models

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

@router.get("", response_model=List[schemas.JobListingResponse])
async def get_jobs(
    keyword: Optional[str] = Query(None, description="Search term for job title or description"),
    location: Optional[str] = Query(None, description="Filter by location"),
    job_type: Optional[str] = Query(None, description="Filter by job type (Full-time, Part-time, Internship, Remote)"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve active job listings filterable by keyword, location, and job type (Public access)."""
    return await crud.get_job_listings(
        db,
        keyword=keyword,
        location=location,
        job_type=job_type,
        limit=limit,
        offset=offset
    )

@router.get("/{id}", response_model=schemas.JobListingResponse)
async def get_job_by_id(id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve full details of a specific job listing by ID (Public access)."""
    job = await crud.get_job_listing(db, job_id=id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job listing with ID {id} not found"
        )
    return job

@router.post("", response_model=schemas.JobListingResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: schemas.JobListingCreate,
    current_user: models.User = Depends(auth.RoleChecker(["employer", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job opportunity listing. Restricted to Employers/Admins."""
    return await crud.create_job_listing(db, job_in=job_in, employer_id=current_user.id)

@router.put("/{id}", response_model=schemas.JobListingResponse)
async def update_job(
    id: int,
    job_in: schemas.JobListingUpdate,
    current_user: models.User = Depends(auth.RoleChecker(["employer", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Update details of an existing job listing. Restricted to the owning Employer or an Admin."""
    job = await crud.get_job_listing(db, job_id=id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job listing with ID {id} not found"
        )
        
    if current_user.role != "admin" and job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this job listing"
        )
        
    return await crud.update_job_listing(db, job=job, job_in=job_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    id: int,
    current_user: models.User = Depends(auth.RoleChecker(["employer", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Delete/Close a job listing. Restricted to the owning Employer or an Admin."""
    job = await crud.get_job_listing(db, job_id=id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job listing with ID {id} not found"
        )
        
    if current_user.role != "admin" and job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this job listing"
        )
        
    await crud.delete_job_listing(db, job=job)
    return
