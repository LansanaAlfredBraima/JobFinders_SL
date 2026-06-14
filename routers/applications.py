import os
import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from database import get_db
import crud
import schemas
import auth
import models
from config import settings

router = APIRouter(tags=["Applications"])

def sanitize_filename(filename: str) -> str:
    """Sanitize the uploaded file's name to prevent path traversal and shell injection."""
    name, ext = os.path.splitext(filename)
    # Remove non-alphanumeric, underscore, hyphen or space characters
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    if not name:
        name = "resume"
    # Ensure extension is lowercase pdf
    ext = ".pdf"
    # Append short unique suffix to avoid collisions
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{name}_{unique_suffix}{ext}"

@router.post("/api/v1/jobs/{job_id}/apply", response_model=schemas.ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_job(
    job_id: int,
    cover_letter: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.RoleChecker(["seeker"])),
    db: AsyncSession = Depends(get_db)
):
    """Submit a job application with a secure PDF resume upload. Restricted to Seekers."""
    # 1. Verify Job Listing exists and is active
    job = await crud.get_job_listing(db, job_id=job_id)
    if not job or not job.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job opportunity does not exist or is no longer active"
        )
    
    # 2. Validate file type (only PDFs allowed)
    if file.content_type != "application/pdf" or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are allowed as resume uploads"
        )
        
    # 3. Validate file size (max 5MB by default) by reading content
    try:
        content = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file"
        )
    file_size = len(content)
    
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB}MB"
        )
        
    # 4. Sanitize and save the file
    sanitized_name = sanitize_filename(file.filename)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, sanitized_name)
    
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving the resume file"
        )
        
    # 5. Save the database record
    resume_url = f"/uploads/{sanitized_name}"
    return await crud.create_application(
        db,
        job_id=job_id,
        seeker_id=current_user.id,
        resume_url=resume_url,
        cover_letter=cover_letter
    )

@router.get("/api/v1/applications", response_model=List[schemas.ApplicationResponse])
async def list_applications(
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve submitted applications.
    
    Seekers see their own applications.
    Employers see applications for their posted jobs.
    Admins see all applications.
    """
    if current_user.role == "seeker":
        return await crud.get_applications_for_seeker(db, seeker_id=current_user.id)
    elif current_user.role == "employer":
        return await crud.get_applications_for_employer_jobs(db, employer_id=current_user.id)
    elif current_user.role == "admin":
        # Return all applications in system
        from sqlalchemy.future import select
        from sqlalchemy.orm import selectinload
        query = select(models.Application).options(selectinload(models.Application.job)).order_by(models.Application.applied_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user role"
        )

@router.patch("/api/v1/applications/{id}", response_model=schemas.ApplicationResponse)
async def update_status(
    id: int,
    status_update: schemas.ApplicationUpdateStatus,
    current_user: models.User = Depends(auth.RoleChecker(["employer", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Update status of a job application. Restricted to the owning Employer or Admin."""
    application = await crud.get_application(db, app_id=id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID {id} not found"
        )
        
    # Verify authorization: current employer must own the job listing, or be an admin
    if current_user.role != "admin" and application.job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update the status of this application"
        )
        
    # Validate status transitions
    allowed_statuses = ["applied", "interviewing", "accepted", "rejected"]
    if status_update.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {allowed_statuses}"
        )
        
    return await crud.update_application_status(db, application=application, status=status_update.status)
