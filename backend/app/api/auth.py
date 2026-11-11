from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import User, Organization, OrganizationMember, generate_uuid
from backend.app.schemas.all_schemas import UserRegister, UserLogin, Token, UserResponse
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin
)
from backend.app.core.logging import log_activity

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Check or create default Organization
    org_name = user_in.organization_name or "Acme CyberSec"
    slug = org_name.lower().replace(" ", "-")
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        org = Organization(
            name=org_name,
            slug=slug,
            description="Default Organization"
        )
        db.add(org)
        db.flush()

    # Determine user role
    role = "admin" if user_in.role == "admin" else "developer"

    new_user = User(
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # Add to organization members
    member = OrganizationMember(
        organization_id=org.id,
        user_id=new_user.id,
        role=role
    )
    db.add(member)
    db.commit()
    db.refresh(new_user)

    log_activity(
        db,
        action="AUTH_REGISTER",
        entity_type="USER",
        entity_id=new_user.id,
        user_id=new_user.id,
        organization_id=org.id,
        details=f"User registered with role {role}"
    )

    token = create_access_token(
        subject=new_user.id,
        role=new_user.role,
        org_id=org.id
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        organization_id=org.id
    )

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email.lower()).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")

    # Get primary organization
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    org_id = membership.organization_id if membership else None

    log_activity(
        db,
        action="AUTH_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        user_id=user.id,
        organization_id=org_id,
        details="User logged in successfully"
    )

    token = create_access_token(
        subject=user.id,
        role=user.role,
        org_id=org_id
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=org_id
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", dependencies=[Depends(require_admin)])
def list_organization_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [{
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at
    } for u in users]
