from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from engine.models import (
    UserModel,
    UserWorkspaceModel,
    CredentialModel,
    UserCredentialModel,
    RoleModel,
    WorkspaceModel,
    PermissionModel
)
from seeder.dependencies.logging import logger
from engine.utils.encryption_util import encrypt
from datetime import date
import re
from typing import Optional, Dict, Any


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    return len(phone) >= 9


def get_valid_input(prompt: str, validator: Optional[callable] = None) -> str:
    """Get valid input from user with optional validation."""
    while True:
        value = input(prompt).strip()
        if not value:
            print("This field cannot be empty. Please try again.")
            continue
        if validator and not validator(value):
            print("Invalid format. Please try again.")
            continue
        return value

    return ""


def get_optional_input(prompt: str, validator: Optional[callable] = None) -> Optional[str]:
    """Get optional input from user with optional validation."""
    while True:
        value = input(f"{prompt} (press Enter to skip): ").strip()
        if not value:
            return None
        if validator and not validator(value):
            print("Invalid format. Please try again.")
            return None
        return value


async def collect_user_data() -> Dict[str, Any]:
    """Collect all user data from prompts."""
    print("\n=== Super User Creation Form ===")
    print("This will create a new super user with admin privileges.")
    print("Please provide the following information:\n")

    # Get required fields
    first_name = get_valid_input("Enter first name: ")
    last_name = get_valid_input("Enter last name: ")
    email = get_valid_input("Enter email: ", validate_email)
    phone = get_valid_input("Enter phone number: ", validate_phone)
    password = get_valid_input("Enter password: ")

    # Get optional fields
    sex = get_optional_input("Enter sex (M/F): ")
    id_number = get_optional_input("Enter ID number: ")
    id_type = get_optional_input("Enter ID type: ")
    date_of_birth_str = get_optional_input("Enter date of birth (YYYY-MM-DD): ")

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "password": password,
        "sex": sex,
        "id_number": id_number,
        "id_type": id_type,
        "date_of_birth_str": date_of_birth_str
    }


async def validate_and_create_user(session: AsyncSession, user_data: Dict[str, Any]) -> bool:
    """Validate user data and create user if valid."""
    try:
        print("\nValidating user data...")

        # Check if user already exists by email or phone
        stmt = select(UserModel).where(
            (UserModel.email == user_data["email"]) |
            (UserModel.phone == user_data["phone"])
        )
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"\nError: User already exists with email {user_data['email']} or phone {user_data['phone']}")
            return False

        # Check if SuperAdmin role exists
        stmt = select(RoleModel).where(RoleModel.name == "SuperAdmin")
        result = await session.execute(stmt)
        super_admin_role = result.scalar_one_or_none()

        if not super_admin_role:
            print("\nError: SuperAdmin role not found. Please run role seeder first.")
            return False
        print("✓ SuperAdmin role found")

        # Check if All permission exists
        stmt = select(PermissionModel).where(PermissionModel.code == "*")
        result = await session.execute(stmt)
        all_permission = result.scalar_one_or_none()

        if not all_permission:
            print("\nError: All permission not found. Please run role seeder first.")
            return False
        print("✓ All permission found")

        # Check if Admin workspace exists
        stmt = select(WorkspaceModel).where(WorkspaceModel.name == "Admin")
        result = await session.execute(stmt)
        admin_workspace = result.scalar_one_or_none()

        if not admin_workspace:
            print("\nError: Admin workspace not found. Please run workspace seeder first.")
            return False
        print("✓ Admin workspace found")

        print("\nCreating user...")
        # Create user
        user = UserModel(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            phone=user_data["phone"],
            sex=user_data["sex"],
            id_number=user_data["id_number"],
            id_type=user_data["id_type"],
            date_of_birth=date.fromisoformat(user_data["date_of_birth_str"]) if user_data["date_of_birth_str"] else None
        )
        session.add(user)
        await session.flush()
        print(f"✓ User created with ID: {user.id}")
        logger.info(f"Added super user: {user_data['email']}")

        print("\nCreating credentials...")
        # Create credentials using the encryption utility
        password_hash, salt = encrypt(user_data["password"])

        print(f"Debug - Salt length: {len(salt)}")
        print(f"Debug - Password hash length: {len(password_hash)}")
        print(f"Debug - Password being hashed: {user_data['password']}")

        credential = CredentialModel(
            password_hash=password_hash,
            salt=salt,
            type="password"
        )
        session.add(credential)
        await session.flush()
        print(f"✓ Credentials created with ID: {credential.id}")
        print(f"Debug - Credential type: {credential.type}")
        print(f"Debug - Credential hash: {credential.password_hash[:10]}...")
        print(f"Debug - Credential salt: {credential.salt[:10]}...")

        # Create user credential relationship
        user_credential = UserCredentialModel(
            user_id=user.id,
            credential_id=credential.id
        )
        session.add(user_credential)
        print("✓ User credential relationship created")

        # Create user workspace relationship with existing Admin workspace
        user_workspace = UserWorkspaceModel(
            user_id=user.id,
            workspace_id=admin_workspace.id,
            role_id=super_admin_role.id,
            is_default=True
        )
        session.add(user_workspace)
        print("✓ User workspace relationship created")
        logger.info(f"Added super user workspace relationship for: {user_data['email']}")

        print("\nCommitting changes...")
        await session.commit()
        print("✓ All changes committed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during super user creation: {str(e)}")
        print(f"\nError: {str(e)}")
        await session.rollback()
        return False


async def seeder(session: AsyncSession):
    """
    Interactive super user creation that prompts for user information.
    This seeder requires SuperAdmin role, All permissions, and Admin workspace to exist in the database.

    Args:
        session (AsyncSession): The database session to use for seeding
    """
    try:
        # First collect all user data
        user_data = await collect_user_data()

        # Then validate and create user
        success = await validate_and_create_user(session, user_data)

        if success:
            print("\nSuper user created successfully!")
            logger.info("Super user creation completed successfully")
        else:
            print("\nSuper user creation failed. Please check the error messages above.")
            logger.error("Super user creation failed")

    except Exception as e:
        error_msg = f"Error during super user creation: {str(e)}"
        print(f"\n{error_msg}")
        logger.error(error_msg)
        raise
