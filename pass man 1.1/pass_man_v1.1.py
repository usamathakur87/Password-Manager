import pandas as pd
import datetime
import pickle
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import logging

# Setup logging to file
logging.basicConfig(filename='app_debug.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load CSV data
def load_csv(file_path):
    try:
        data = pd.read_csv(file_path)
        data.columns = [col.strip().lower().replace(' ', '_') for col in data.columns]  # Normalize column names
        return data
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while loading the file: {e}")
        logging.error(f"Error loading CSV file: {e}")
        return None

# Add Supplier from CSV or Excel file
def add_supplier_from_file(file_path):
    suppliers = load_csv(file_path)
    if suppliers is None:
        return None
    suppliers = suppliers[['supplier_name', 'user_id', 'password', 'office_id', 'site_url']]  # Keep only required columns
    suppliers.fillna('', inplace=True)  # Replace NaNs with empty strings
    return suppliers

# Add Supplier Manually
def add_supplier_manually():
    supplier = {}
    supplier['supplier_name'] = simpledialog.askstring("Input", "Enter Supplier Name:")
    supplier['site_url'] = simpledialog.askstring("Input", "Enter Site URL:")
    supplier['user_id'] = simpledialog.askstring("Input", "Enter User ID:")
    supplier['password'] = simpledialog.askstring("Input", "Enter Password:")
    supplier['office_id'] = simpledialog.askstring("Input", "Enter Office ID (leave blank if not applicable):")
    supplier['expiry_date'] = datetime.datetime.now() + datetime.timedelta(days=30)
    supplier['reminder_date'] = supplier['expiry_date'] - datetime.timedelta(days=7)
    return pd.DataFrame([supplier])

# Registration
def register(users):
    username = simpledialog.askstring("Registration", "Enter your username:")
    if username in users:
        messagebox.showwarning("Warning", "Username already taken, please try again.")
        logging.warning(f"Username '{username}' is already taken.")
    else:
        password = simpledialog.askstring("Registration", "Enter your password:", show='*')
        users[username] = password
        messagebox.showinfo("Success", "Registration successful.")
        logging.info(f"User '{username}' registered successfully.")
    return users

# Sign In
def sign_in(users):
    username = simpledialog.askstring("Sign In", "Enter your username:")
    if username not in users:
        messagebox.showwarning("Warning", "Username not found. Please register first.")
        logging.warning(f"Username '{username}' not found during sign-in.")
        return None
    password = simpledialog.askstring("Sign In", "Enter your password:", show='*')
    if users[username] == password:
        logging.info(f"User '{username}' signed in successfully.")
        return username
    else:
        messagebox.showerror("Error", "Incorrect password.")
        logging.error(f"Incorrect password attempt for user '{username}'.")
        return None

# Save data to file
def save_data(users, suppliers):
    with open('users.pkl', 'wb') as user_file:
        pickle.dump(users, user_file)
    suppliers.to_pickle('suppliers.pkl')
    logging.info("Data saved successfully.")

# Load data from file
def load_data():
    try:
        with open('users.pkl', 'rb') as user_file:
            users = pickle.load(user_file)
        logging.info("User data loaded successfully.")
    except FileNotFoundError:
        users = {}
        logging.warning("User data file not found. Starting with empty user data.")
    try:
        suppliers = pd.read_pickle('suppliers.pkl')
        logging.info("Supplier data loaded successfully.")
    except FileNotFoundError:
        suppliers = pd.DataFrame(columns=['supplier_name', 'user_id', 'password', 'office_id', 'site_url', 'expiry_date', 'reminder_date'])
        logging.warning("Supplier data file not found. Starting with empty supplier data.")
    return users, suppliers

# Main Application Class
class PasswordManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Manager")
        self.users, self.suppliers = load_data()
        self.current_user = None

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=20)

        self.init_main_menu()

    def init_main_menu(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        tk.Label(self.main_frame, text="Password Manager:").pack()
        tk.Button(self.main_frame, text="[1] To Register", command=self.register).pack(pady=5)
        tk.Button(self.main_frame, text="[2] To Sign in", command=self.sign_in).pack(pady=5)
        tk.Button(self.main_frame, text="[3] To Exit", command=self.exit_app).pack(pady=5)

    def register(self):
        self.users = register(self.users)

    def sign_in(self):
        self.current_user = sign_in(self.users)
        if self.current_user:
            self.init_password_manager()

    def init_password_manager(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        tk.Label(self.main_frame, text="Password Manager").pack()
        tk.Button(self.main_frame, text="1. View Supplier Details", command=self.view_supplier_details).pack(pady=5)
        tk.Button(self.main_frame, text="2. Modify Supplier", command=self.modify_supplier).pack(pady=5)
        tk.Button(self.main_frame, text="3. Add New Supplier", command=self.add_new_supplier).pack(pady=5)
        tk.Button(self.main_frame, text="4. Exit", command=self.exit_app).pack(pady=5)

    def view_supplier_details(self):
        supplier_list = self.suppliers[['supplier_name']].reset_index(drop=True).rename_axis('S.No').reset_index()
        supplier_no = simpledialog.askinteger("View Supplier", f"Suppliers List:\n{supplier_list}\n\nEnter the S.No to view details:")
        if supplier_no is not None and supplier_no in range(len(self.suppliers)):
            supplier_details = self.suppliers.iloc[supplier_no]
            messagebox.showinfo("Supplier Details", f"Supplier: {supplier_details['supplier_name']}\nUser ID: {supplier_details['user_id']}\nPassword: {supplier_details['password']}\nSite URL: {supplier_details['site_url']}\nLast Reset: {supplier_details['expiry_date']}\nPassword Reset Reminder: {supplier_details['reminder_date']}")
            logging.info(f"Displayed details for supplier '{supplier_details['supplier_name']}'.")
        else:
            messagebox.showerror("Error", "Invalid S.No.")
            logging.error(f"Invalid S.No. entered for viewing supplier details: {supplier_no}")

    def modify_supplier(self):
        supplier_list = self.suppliers[['supplier_name']].reset_index(drop=True).rename_axis('S.No').reset_index()
        to_modify = simpledialog.askinteger("Modify Supplier", f"Suppliers List:\n{supplier_list}\n\nEnter the S.No to modify:")
        if to_modify is not None and to_modify in range(len(self.suppliers)):
            field = simpledialog.askstring("Modify Supplier", "Which field do you want to modify? (supplier_name/user_id/password/office_id/site_url):")
            new_value = simpledialog.askstring("Modify Supplier", f"Enter new value for {field}:")
            if field and new_value:
                self.suppliers.loc[to_modify, field] = new_value
                if field == 'password':
                    self.suppliers.loc[to_modify, 'expiry_date'] = datetime.datetime.now() + datetime.timedelta(days=30)
                    self.suppliers.loc[to_modify, 'reminder_date'] = self.suppliers.loc[to_modify, 'expiry_date'] - datetime.timedelta(days=7)
                messagebox.showinfo("Success", "Supplier updated successfully.")
                logging.info(f"Updated field '{field}' for supplier '{self.suppliers.loc[to_modify, 'supplier_name']}' with new value '{new_value}'.")
            else:
                messagebox.showerror("Error", "Invalid field or value.")
                logging.error("Invalid field or value entered during supplier modification.")
        else:
            messagebox.showerror("Error", "Supplier not found.")
            logging.error(f"Supplier not found for modification: S.No {to_modify}")

    def add_new_supplier(self):
        method = simpledialog.askstring("Add Supplier", "Do you want to add suppliers manually (m), or through a CSV file (c)?")
        if method == 'm':
            new_supplier = add_supplier_manually()
            if not new_supplier.empty:
                self.suppliers = pd.concat([self.suppliers, new_supplier], ignore_index=True)
            messagebox.showinfo("Success", "Supplier added successfully.")
            logging.info("New supplier added manually.")
        elif method == 'c':
            file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV files", "*.csv")])
            if file_path:
                new_suppliers = add_supplier_from_file(file_path)
                if new_suppliers is not None and not new_suppliers.empty:
                    new_suppliers = new_suppliers.dropna(axis=1, how='all')  # Drop all-NA columns
                    new_suppliers['expiry_date'] = datetime.datetime.now() + datetime.timedelta(days=30)
                    new_suppliers['reminder_date'] = new_suppliers['expiry_date'] - datetime.timedelta(days=7)
                    self.suppliers = pd.concat([self.suppliers, new_suppliers], ignore_index=True)
                    messagebox.showinfo("Success", "Suppliers added successfully.")
                    logging.info("New suppliers added from CSV file.")

    def exit_app(self):
        save_data(self.users, self.suppliers)
        logging.info("Application exited successfully.")
        self.root.quit()

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManagerApp(root)
    root.mainloop()
