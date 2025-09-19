#!/usr/bin/env python3
"""
Create initial admin user script.
Run this script to create the first admin user for FrozenBot.
"""

import asyncio
import sys
from getpass import getpass
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User, UserRole
from app.utils.security import hash_password, validate_password
from app.database import Base


async def create_admin_user():
    """Create initial admin user."""
    print("=== FrozenBot Admin User Creation ===\n")

    # Get user input
    print("Creating initial admin user...")
    username = input("Username: ").strip()

    if not username:
        print("Username is required!")
        return False

    if len(username) < 3:
        print("Username must be at least 3 characters long!")
        return False

    first_name = input("First name: ").strip()
    if not first_name:
        print("First name is required!")
        return False

    last_name = input("Last name (optional): ").strip() or None
    email = input("Email (optional): ").strip() or None

    # Password input with validation
    while True:
        password = getpass("Password: ")
        password_confirm = getpass("Confirm password: ")

        if password != password_confirm:
            print("Passwords don't match! Please try again.\n")
            continue

        # Validate password
        validation = validate_password(password)
        if not validation["valid"]:
            print(f"Password is not strong enough:")
            for error in validation["errors"]:
                print(f"  - {error}")
            print()
            continue

        print(f"Password strength: {validation['strength']}")
        break

    # Create database connection
    print("\nConnecting to database...")
    engine = create_async_engine(settings.database_url)

    try:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create async session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as db:
            # Check if admin already exists
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"User with username '{username}' already exists!")
                return False

            # Check if email already exists
            if email:
                result = await db.execute(
                    select(User).where(User.email == email)
                )
                existing_email = result.scalar_one_or_none()

                if existing_email:
                    print(f"User with email '{email}' already exists!")
                    return False

            # Create admin user
            admin_user = User(
                telegram_id=0,  # Will be updated when admin connects Telegram
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
                is_admin=True,
                is_active=True
            )

            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)

            print(f"\n✅ Admin user created successfully!")
            print(f"User ID: {admin_user.id}")
            print(f"Username: {admin_user.username}")
            print(f"Role: {admin_user.role.value}")
            print(f"Email: {admin_user.email or 'Not set'}")
            print(f"Full name: {admin_user.full_name}")

            print(f"\n🔐 You can now login with:")
            print(f"Username: {admin_user.username}")
            print(f"Password: <your password>")

            return True

    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        return False

    finally:
        await engine.dispose()


async def list_admin_users():
    """List existing admin users."""
    print("=== Existing Admin Users ===\n")

    engine = create_async_engine(settings.database_url)

    try:
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(
                    User.role.in_([UserRole.ADMIN, UserRole.MANAGER])
                ).order_by(User.created_at)
            )
            users = result.scalars().all()

            if not users:
                print("No admin/manager users found.")
                return

            for user in users:
                print(f"ID: {user.id}")
                print(f"Username: {user.username}")
                print(f"Role: {user.role.value}")
                print(f"Email: {user.email or 'Not set'}")
                print(f"Full name: {user.full_name}")
                print(f"Active: {user.is_active}")
                print(f"Created: {user.created_at}")
                print("-" * 50)

    except Exception as e:
        print(f"Error listing users: {e}")

    finally:
        await engine.dispose()


async def reset_admin_password():
    """Reset admin password."""
    print("=== Reset Admin Password ===\n")

    username = input("Username: ").strip()
    if not username:
        print("Username is required!")
        return False

    # Password input with validation
    while True:
        password = getpass("New password: ")
        password_confirm = getpass("Confirm new password: ")

        if password != password_confirm:
            print("Passwords don't match! Please try again.\n")
            continue

        # Validate password
        validation = validate_password(password)
        if not validation["valid"]:
            print(f"Password is not strong enough:")
            for error in validation["errors"]:
                print(f"  - {error}")
            print()
            continue

        print(f"Password strength: {validation['strength']}")
        break

    engine = create_async_engine(settings.database_url)

    try:
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            if not user:
                print(f"User with username '{username}' not found!")
                return False

            if user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
                print(f"User '{username}' is not an admin or manager!")
                return False

            # Update password
            user.password_hash = hash_password(password)
            user.failed_login_attempts = 0  # Reset failed attempts
            user.locked_until = None  # Unlock account

            await db.commit()

            print(f"\n✅ Password updated successfully for user '{username}'!")
            return True

    except Exception as e:
        print(f"Error resetting password: {e}")
        return False

    finally:
        await engine.dispose()


def print_menu():
    """Print menu options."""
    print("\n=== FrozenBot Admin Management ===")
    print("1. Create admin user")
    print("2. List admin users")
    print("3. Reset admin password")
    print("4. Exit")
    print("=" * 35)


async def main():
    """Main function."""
    while True:
        print_menu()
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            await create_admin_user()
        elif choice == "2":
            await list_admin_users()
        elif choice == "3":
            await reset_admin_password()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please enter 1-4.")

        if choice in ["1", "2", "3"]:
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)