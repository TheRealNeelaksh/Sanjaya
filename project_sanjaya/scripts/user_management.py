import requests
import getpass
import argparse

API_URL = "http://127.0.0.1:8000"
TOKEN = ""

def login_admin(username, password):
    """Logs in the admin user and returns a JWT token."""
    global TOKEN
    response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    if response.status_code == 200:
        TOKEN = response.json()["access_token"]
        return True
    return False

def get_headers():
    """Returns the authorization headers for API requests."""
    return {"Authorization": f"Bearer {TOKEN}"}

def create_user(args):
    """Creates a new user."""
    response = requests.post(f"{API_URL}/register", json={"username": args.username, "password": args.password, "role": args.role})
    if response.status_code == 200:
        print(f"User '{args.username}' created successfully.")
    else:
        print(f"Error creating user: {response.json()['detail']}")

def delete_user(args):
    """Deletes a user."""
    response = requests.delete(f"{API_URL}/users/{args.username}", headers=get_headers())
    if response.status_code == 200:
        print(f"User '{args.username}' deleted successfully.")
    else:
        print(f"Error deleting user: {response.json()['detail']}")

def list_users(args):
    """Lists all users."""
    response = requests.get(f"{API_URL}/users", headers=get_headers())
    if response.status_code == 200:
        users = response.json()
        for user in users:
            print(f"ID: {user['id']}, Username: {user['username']}, Role: {user['role']}")
    else:
        print(f"Error listing users: {response.json()['detail']}")

def change_password(args):
    """Changes a user's password."""
    response = requests.put(f"{API_URL}/users/password", json={"username": args.username, "new_password": args.new_password}, headers=get_headers())
    if response.status_code == 200:
        print(f"Password for user '{args.username}' changed successfully.")
    else:
        print(f"Error changing password: {response.json()['detail']}")

def main():
    """Main function to handle user management operations."""
    parser = argparse.ArgumentParser(description="User Management Script for Project Sanjaya")
    subparsers = parser.add_subparsers(dest="command")

    # Create user command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("username", help="The username for the new user")
    create_parser.add_argument("password", help="The password for the new user")
    create_parser.add_argument("role", choices=["parent", "child"], help="The role of the new user")
    create_parser.set_defaults(func=create_user)

    # Delete user command
    delete_parser = subparsers.add_parser("delete", help="Delete a user")
    delete_parser.add_argument("username", help="The username of the user to delete")
    delete_parser.set_defaults(func=delete_user)

    # List users command
    list_parser = subparsers.add_parser("list", help="List all users")
    list_parser.set_defaults(func=list_users)

    # Change password command
    change_password_parser = subparsers.add_parser("change-password", help="Change a user's password")
    change_password_parser.add_argument("username", help="The username of the user")
    change_password_parser.add_argument("new_password", help="The new password")
    change_password_parser.set_defaults(func=change_password)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    admin_username = input("Enter admin username: ")
    admin_password = getpass.getpass("Enter admin password: ")

    if not login_admin(admin_username, admin_password):
        print("Admin login failed.")
        return

    args.func(args)

if __name__ == "__main__":
    main()
