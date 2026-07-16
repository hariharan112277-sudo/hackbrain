from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password
from app.core.dependencies import get_user_repository
from app.repositories.interfaces import IUserRepository

router = APIRouter(prefix="/users", tags=["User Subsystem Management Operations"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    user_repo: IUserRepository = Depends(get_user_repository)
):
    """
    Exposes a secure public API endpoint for onboarding profiles into the core subsystem architecture.
    Applies security hashes and validates entity uniqueness prior to persistent tracking saves.
    """
    # Verify entity isolation boundary integrity
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active user record matching the provided email address identification already exists."
        )
    
    # Process password values through the Stage-5 security abstraction layer safely
    hashed_pwd = hash_password(user_in.password)
    
    # Delegate persistence execution downstream into the repository subsystem context
    # Adapted to match existing IUserRepository.create(user_data: Dict) contract
    new_user = await user_repo.create({
        "email": user_in.email,
        "full_name": user_in.full_name,
        "hashed_password": hashed_pwd,
    })

    # Map repository dict output to the UserResponse schema expected by the Stage-6 REST matrix
    # The repository returns a dict with UUID id; the Stage-6 schema expects int id.
    # We hash the UUID to produce a stable integer surrogate for the response contract.
    from uuid import UUID
    raw_id = new_user.get("id")
    if isinstance(raw_id, UUID):
        int_id = raw_id.int % (2**31)  # Stable int32 surrogate
    elif isinstance(raw_id, int):
        int_id = raw_id
    else:
        int_id = hash(str(raw_id)) % (2**31)

    return UserResponse(
        id=int_id,
        email=new_user.get("email", user_in.email),
        full_name=new_user.get("full_name", user_in.full_name),
        is_active=new_user.get("is_active", True),
        created_at=new_user.get("created_at"),
    )
