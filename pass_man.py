import time
import json
import random
import string
from datetime import datetime, timedelta

# File to store supplier data
DATA_FILE = "suppliers.json"

def load_data():
    """Load supplier data from file."""
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    """Save supplier data to file."""
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def user_registration():
    """Register or sign in to access the program."""
    users = load_data().get("users", {})
    print("Welcome! Please register or sign in.")
    while True:
        choice = input("Do you want to register (r) or sign in (s)? ").lower()
        if choice == "r":
            username = input("Enter a new username: ")
            if username in users:
                print("Username already exists. Try signing in.")
                continue
            password = input("Enter a new password: ")
            users[username] = password
            data = load_data()
            data["users"] = users
            save_data(data)
            print("Registration successful. You can now sign in.")
        elif choice == "s":
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            if users.get(username) == password:
                print("Access granted!")
                return True
            else:
                print("Incorrect username or password. Try again.")
        else:
            print("Invalid choice. Please enter 'r' to register or 's' to sign in.")

def generate_password():
    """Generate a random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(12))

def add_supplier(data):
    """Add a new supplier to the data."""
    supplier_name = input("Enter supplier name: ")
    if supplier_name in data:
        print("Supplier already exists. Use modify option to update.")
        return
    
    requires_office_id = input("Does this supplier require an office ID? (yes/no): ").lower() == "yes"
    credentials = {}
    if requires_office_id:
        credentials["office_id"] = input("Enter office ID: ")
    credentials["user_id"] = input("Enter user ID: ")
    credentials["password"] = input("Enter password (leave blank to generate a new one): ") or generate_password()
    credentials["site_url"] = input("Enter site URL: ")
    credentials["last_reset"] = datetime.now().isoformat()
    
    data[supplier_name] = credentials
    print(f"Supplier {supplier_name} added successfully!")

def view_supplier_list(data):
    """View a list of all suppliers."""
    if not data:
        print("No suppliers found.")
    else:
        print("\nSupplier List:")
        for supplier_name in data:
            if supplier_name != "users":
                print(f"- {supplier_name}")

def select_supplier(data):
    """Select a supplier from the list."""
    suppliers = [name for name in data.keys() if name != "users"]
    if not suppliers:
        print("No suppliers found.")
        return None
    
    print("\nSupplier List:")
    for idx, supplier_name in enumerate(suppliers, start=1):
        print(f"{idx}. {supplier_name}")
    
    while True:
        try:
            choice = int(input("Enter the number of the supplier: "))
            if 1 <= choice <= len(suppliers):
                return suppliers[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def view_supplier(data):
    """View supplier details."""
    supplier_name = select_supplier(data)
    if supplier_name:
        credentials = data[supplier_name]
        print(f"\nSupplier: {supplier_name}")
        if "office_id" in credentials:
            print(f"Office ID: {credentials['office_id']}")
        print(f"User ID: {credentials['user_id']}")
        print(f"Password: {credentials['password']}")
        print(f"Site URL: {credentials['site_url']}")
        print(f"Last Reset: {credentials['last_reset']}")

def modify_supplier(data):
    """Modify an existing supplier."""
    supplier_name = select_supplier(data)
    if supplier_name:
        action = input("Do you want to modify (m) or delete (d) this supplier? ").lower()
        if action == "m":
            credentials = data[supplier_name]
            if "office_id" in credentials:
                credentials["office_id"] = input("Enter new office ID (leave blank to keep current): ") or credentials["office_id"]
            credentials["user_id"] = input("Enter new user ID (leave blank to keep current): ") or credentials["user_id"]
            credentials["password"] = input("Enter new password (leave blank to keep current): ") or credentials["password"]
            credentials["site_url"] = input("Enter new site URL (leave blank to keep current): ") or credentials["site_url"]
            credentials["last_reset"] = datetime.now().isoformat()
            print(f"Supplier {supplier_name} updated successfully!")
        elif action == "d":
            del data[supplier_name]
            print(f"Supplier {supplier_name} deleted successfully!")
        else:
            print("Invalid choice. Please enter 'm' to modify or 'd' to delete.")

def check_password_reset_reminder(data):
    """Check if any supplier passwords need resetting or will expire soon."""
    print("\nPassword Reset Reminders:")
    current_time = datetime.now()
    for supplier_name, credentials in data.items():
        if supplier_name == "users":
            continue
        if "last_reset" not in credentials:
            continue
        last_reset = datetime.fromisoformat(credentials["last_reset"])
        time_since_reset = current_time - last_reset
        if time_since_reset >= timedelta(days=30):
            print(f"Supplier {supplier_name} password is due for reset.")
        elif timedelta(days=23) <= time_since_reset < timedelta(days=30):
            print(f"Reminder: Supplier {supplier_name} password will expire in {30 - time_since_reset.days} days.")

def main():
    """Main program loop."""
    if not user_registration():
        return

    data = load_data()
    while True:
        print("\nPassword Manager")
        print("1. View Supplier List")
        print("2. View Supplier Details")
        print("3. Modify Supplier")
        print("4. Add New Supplier")
        print("5. Exit")
        
        choice = input("Enter your choice: ")
        if choice == "1":
            view_supplier_list(data)
        elif choice == "2":
            view_supplier(data)
        elif choice == "3":
            modify_supplier(data)
        elif choice == "4":
            add_supplier(data)
        elif choice == "5":
            save_data(data)
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        check_password_reset_reminder(data)

if __name__ == "__main__":
    main()
