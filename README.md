# 📦 Corporate IT Solutions – License Management System

A full-stack **Python + Streamlit + MySQL** application designed to manage customers, products, software licenses, renewals, and administrative requests.  
Built to streamline internal IT operations, track license lifecycles, and prevent missed renewals.

---

## 🚀 Features

### 🔐 Authentication & Security
- User registration and login
- Secure password hashing (PBKDF2 + salt)
- Role-based access control (Admin / User)

### 📊 Dashboard
- Total customer count
- Active vs expired license metrics
- Pie chart visualisations
- Tables for expired and soon-to-expire licenses (within 21 days)

### 👥 Customer Master
- Add, edit, delete customers
- Interactive tables using AgGrid
- Field validation and safe deletion

### 📦 Product Master
- Manage products and product types
- Default license validity per product

### 📄 License Master
- Add and manage licenses
- Prevent duplicate licenses per customer/product
- Automatic expiry date calculation
- Multi-currency support (ZMW / USD)
- License upgrades (quantity & cost)
- Edit and delete licenses

### 🔍 Customer Product View
- View all licenses by customer
- Filter by customer
- Sorted by expiry date

### 🔄 Renewal Updates
- Full overview of expired licenses
- Licenses expiring within the next 3 weeks
- Renewal status tables

### 📝 Request Form
- Users can submit financial or service requests
- Stored with status tracking

### 🛠 Admin Requests (Admin Only)
- Review pending requests
- Approve or reject requests
- View request history

### ⚙️ User Settings
- Change password
- Change username
- Secure credential verification

---

## 🗂 Project Structure

project-root/
│── app.py
│── Dashboard.py
│── CustomerMaster.py
│── ProductMaster.py
│── LicenseEntry.py
│── CustomerProductView.py
│── RenewalUpdates.py
│── RequestForm.py
│── AdminRequests.py
│── Settings.py
│── requirements.txt
│── images/
│ └── logo.png
└── README.md



---

## 🛠 Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** MySQL
- **Data Handling:** Pandas
- **Charts:** Plotly
- **Tables:** AgGrid
- **Security:** PBKDF2-HMAC (SHA-256)

---

## 📥 Installation

### 1️⃣ Clone the repository
```bash
git clone <repository-url>
cd project-folder




python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows


pip install -r requirements.txt


CREATE DATABASE `Corporate IT Solutions`;



CREATE TABLE USERS (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password TEXT,
    salt TEXT,
    role ENUM('user','admin') DEFAULT 'user'
);



CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(255),
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    location VARCHAR(255)
);


CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255),
    product_type VARCHAR(255),
    default_validity_months INT
);



CREATE TABLE licenses (
    license_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    issue_date DATE,
    installation_date DATE,
    expiry_date DATE,
    validity_period_months INT,
    remarks TEXT,
    kwacha_amount DECIMAL(10,2),
    USD_amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);


CREATE TABLE requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    date DATE,
    topic VARCHAR(255),
    description TEXT,
    currency VARCHAR(10),
    amount DECIMAL(10,2),
    status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


host="localhost"
user="root"
password="root"
database="Corporate IT Solutions"


streamlit run app.py


http://localhost:8501


UPDATE USERS SET role = 'admin' WHERE username = 'your_username';
