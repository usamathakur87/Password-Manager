import os
import csv
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import getpass
import hashlib
import sqlite3

# Database Setup
conn = sqlite3.connect('password_manager.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    email TEXT NOT NULL
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_name TEXT NOT NULL,
                    office_id TEXT,
                    user_id TEXT NOT NULL,
                    password TEXT NOT NULL,
                    site_url TEXT,
                    last_reset TIMESTAMP,
                    reset_reminder TIMESTAMP
                )''')

conn.commit()

# Constants
EMAIL_ID = "it@alfauz.com.pk"
EMAIL_PASSWORD = "As@npw786"
SMTP_SERVER = "mail.alfauz.com.pk"
SMTP_PORT = 587
PASSWORD_EXPIRY_DAYS = 30
RESET_REMINDER_DAYS = 7

# Utility Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ID
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ID, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ID, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

# User Management
def register():
    while True:
        username = input("Enter a username: ")
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print("Username already exists.")
            choice = input("Do you want to: [1] Sign in, [2] Try new username, [3] Exit? ").strip()
            if choice == '1':
                user = sign_in()
                if user:
                    password_manager()
                return
            elif choice == '2':
                continue
            elif choice == '3':
                return
            else:
                print("Invalid choice. Please try again.")
        else:
            password = getpass.getpass("Enter a password: ")
            email = input("Enter your email: ")
            hashed_password = hash_password(password)
            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, hashed_password, email))
            conn.commit()
            print("Registration successful!")
            return

def sign_in():
    username = input("Enter your username: ")
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        print("User not available. Please register first.")
        return None
    while True:
        password = getpass.getpass("Enter your password: ")
        hashed_password = hash_password(password)
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            print("Sign in successful!")
            return username
        else:
            print("Invalid password.")
            reset_choice = input("Do you want to reset your password? (yes/no/exit): ").strip().lower()
            if reset_choice == 'yes':
                reset_password(username)
                return None
            elif reset_choice == 'exit':
                return None
            else:
                print("Please try again.")

def reset_password(username=None):
    if not username:
        username = input("Enter your username: ")
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        email = user[2]
        new_password = getpass.getpass("Enter a new password: ")
        hashed_password = hash_password(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
        conn.commit()
        send_email(email, "Password Reset Notification", "Your password has been reset successfully.")
        print("Password reset successful! A notification has been sent to your email.")
    else:
        print("User does not exist. Please register first.")

# Supplier Management
def view_suppliers():
    cursor.execute("SELECT id, supplier_name FROM suppliers")
    suppliers = cursor.fetchall()
    if not suppliers:
        print("No suppliers added.")
        return
    for supplier in suppliers:
        print(f"{supplier[0]}. {supplier[1]}")
    choice = int(input("Enter the S.No to view details: "))
    cursor.execute("SELECT * FROM suppliers WHERE id = ?", (choice,))
    supplier = cursor.fetchone()
    if supplier:
        print(f"""
Supplier: {supplier[1]}
User ID: {supplier[3]}
Password: {supplier[4]}
Site URL: {supplier[5]}
Last Reset: {supplier[6]}
Password Reset Reminder: {supplier[7]}
        """)

def modify_supplier():
    cursor.execute("SELECT id, supplier_name FROM suppliers")
    suppliers = cursor.fetchall()
    if not suppliers:
        print("No suppliers added.")
        return
    for supplier in suppliers:
        print(f"{supplier[0]}. {supplier[1]}")
    choice = int(input("Enter the S.No to modify: "))
    cursor.execute("SELECT * FROM suppliers WHERE id = ?", (choice,))
    supplier = cursor.fetchone()
    if supplier:
        new_name = input(f"Enter new supplier name (current: {supplier[1]}): ") or supplier[1]
        new_office_id = input(f"Enter new office ID (current: {supplier[2]}): ") or supplier[2]
        new_user_id = input(f"Enter new user ID (current: {supplier[3]}): ") or supplier[3]
        new_password = input(f"Enter new password (current: {supplier[4]}): ") or supplier[4]
        new_site_url = input(f"Enter new site URL (current: {supplier[5]}): ") or supplier[5]
        cursor.execute("""
            UPDATE suppliers
            SET supplier_name = ?, office_id = ?, user_id = ?, password = ?, site_url = ?
            WHERE id = ?
        """, (new_name, new_office_id, new_user_id, new_password, new_site_url, choice))
        conn.commit()
        print("Supplier details updated successfully!")

def add_supplier():
    print("""[1] Using CSV file
[2] Using Excel File
[3] Manually Adding Supplier
[4] Return to Previous Menu""")
    choice = int(input("Enter your choice: "))
    if choice == 1:
        file_path = input("Enter the path to the CSV file: ")
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                add_supplier_to_db(row['supplier_name'], row.get('office_id'), row['user_id'], row['password'], row['site_url'])
    elif choice == 2:
        file_path = input("Enter the path to the Excel file: ")
        df = pd.read_excel(file_path)
        for _, row in df.iterrows():
            add_supplier_to_db(row['supplier_name'], row.get('office_id'), row['user_id'], row['password'], row['site_url'])
    elif choice == 3:
        supplier_name = input("Enter supplier name: ")
        office_id = input("Enter office ID (if applicable): ")
        user_id = input("Enter user ID: ")
        password = input("Enter password: ")
        site_url = input("Enter site URL: ")
        add_supplier_to_db(supplier_name, office_id, user_id, password, site_url)
    elif choice == 4:
        return
    else:
        print("Invalid choice. Please try again.")

def add_supplier_to_db(supplier_name, office_id, user_id, password, site_url):
    last_reset = datetime.now()
    reset_reminder = last_reset + timedelta(days=PASSWORD_EXPIRY_DAYS - RESET_REMINDER_DAYS)
    cursor.execute("""
        INSERT INTO suppliers (supplier_name, office_id, user_id, password, site_url, last_reset, reset_reminder)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (supplier_name, office_id, user_id, password, site_url, last_reset, reset_reminder))
    conn.commit()
    print(f"Supplier '{supplier_name}' added successfully!")

def view_password_reminder_alert():
    cursor.execute("SELECT id, supplier_name, reset_reminder FROM suppliers WHERE reset_reminder <= ?", (datetime.now() + timedelta(days=RESET_REMINDER_DAYS),))
    suppliers = cursor.fetchall()
    if not suppliers:
        print("No suppliers need resetting at the moment.")
        return
    for supplier in suppliers:
        print(f"{supplier[0]}. {supplier[1]} - Reset Reminder: {supplier[2]}")

# Main Program
def main():
    while True:
        print("""
Password Manager!
Welcome! Please register or sign in.
[1] To Register
[2] To Sign in
[3] To Exit
        """)
        choice = int(input("Enter your choice: "))
        if choice == 1:
            register()
        elif choice == 2:
            user = sign_in()
            if user:
                password_manager()
        elif choice == 3:
            break
        else:
            print("Invalid choice. Please try again.")

def password_manager():
    cursor.execute("SELECT COUNT(*) FROM suppliers WHERE reset_reminder <= ?", (datetime.now() + timedelta(days=RESET_REMINDER_DAYS),))
    reminder_count = cursor.fetchone()[0]
    while True:
        print(f"""
Password Manager
1. View Supplier Details
2. Modify Supplier
3. Add New Supplier
4. View Supplier Password Reminder Alert ({reminder_count} suppliers need resetting)
5. Exit
        """)
        choice = int(input("Enter your choice: "))
        if choice == 1:
            view_suppliers()
        elif choice == 2:
            modify_supplier()
        elif choice == 3:
            add_supplier()
        elif choice == 4:
            view_password_reminder_alert()
        elif choice == 5:
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

# Close the database connection
conn.close()
