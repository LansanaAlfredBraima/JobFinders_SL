from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import crud
import schemas
import auth
import models
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user (Seeker or Employer). Seeker profiles are automatically initialized."""
    # Check if username exists
    db_user = await crud.get_user_by_username(db, username=user_in.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # Check if email exists
    db_email = await crud.get_user_by_email(db, email=user_in.email)
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    # Validate role
    if user_in.role not in ["seeker", "employer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'seeker', 'employer', or 'admin'."
        )
    
    return await crud.create_user(db, user_in)

@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate credentials (username or email) and issue a stateful bearer JWT token."""
    # Verify username
    user = await crud.get_user_by_username(db, form_data.username)
    if not user:
        # Fallback to email if user typed email instead of username
        user = await crud.get_user_by_email(db, form_data.username)
        
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username
    }

@router.get("/me", response_model=schemas.UserResponseWithProfile)
async def read_users_me(
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed metadata of the currently authenticated user session."""
    profile_data = None
    if current_user.role == "seeker":
        profile = await crud.get_profile_by_user_id(db, current_user.id)
        if profile:
            profile_data = schemas.SeekerProfileResponse.model_validate(profile)
            
    return schemas.UserResponseWithProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at,
        seeker_profile=profile_data
    )

@router.put("/profile", response_model=schemas.SeekerProfileResponse)
async def update_seeker_profile(
    profile_in: schemas.SeekerProfileUpdate,
    current_user: models.User = Depends(auth.RoleChecker(["seeker"])),
    db: AsyncSession = Depends(get_db)
):
    """Update details in the current seeker's profile."""
    profile = await crud.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seeker profile not found"
        )
    return await crud.update_profile(db, profile, profile_in)

@router.post("/profile/resume", response_model=schemas.SeekerProfileResponse)
async def upload_profile_resume(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.RoleChecker(["seeker"])),
    db: AsyncSession = Depends(get_db)
):
    """Upload a PDF resume for the seeker profile."""
    import os
    import uuid
    import re

    # 1. Verify Seeker Profile exists
    profile = await crud.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seeker profile not found"
        )

    # 2. Validate file type (only PDFs allowed)
    if file.content_type != "application/pdf" or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are allowed as resume uploads"
        )
        
    # 3. Validate file size (max 5MB by default)
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
    name, ext = os.path.splitext(file.filename)
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    name = name.replace(' ', '_')
    if not name:
        name = "profile_resume"
    unique_suffix = uuid.uuid4().hex[:8]
    sanitized_name = f"{name}_{unique_suffix}.pdf"
    
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
        
    # 5. Update the profile resume_url in the database
    resume_url = f"/uploads/{sanitized_name}"
    profile_update = schemas.SeekerProfileUpdate(resume_url=resume_url)
    return await crud.update_profile(db, profile, profile_update)
