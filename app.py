# app.py

import streamlit as st
from altair.vega import title
from LicenseEntry import show_license_entry
from Dashboard import show_dashboard
import mysql.connector
from mysql.connector import Error
import pandas as pd
import hashlib
import secrets

def generate_salt():
    return secrets.token_hex(16)

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()

def verify_password(stored_password, stored_salt, provided_password):
    return stored_password == hash_password(provided_password, stored_salt)


# --- DB CONNECTION ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="Corporate IT Solutions"
        )
    except Error as e:
        st.error(f"Database error: {e}")
        return None


# --- LOGIN & REGISTER ---
def username_exists(username):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM USERS WHERE username = %s", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    return False


def register_user(username, email, password, role='user'):
    conn = get_db_connection()
    if conn:
        try:
            # Check if username or email already exists
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM USERS WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                return False, "Username or email already exists"

            # Generate salt and hash password
            salt = generate_salt()
            hashed_password = hash_password(password, salt)

            cursor.execute(
                "INSERT INTO USERS (username, email, password, salt, role) VALUES (%s, %s, %s, %s, %s)",
                (username, email, hashed_password, salt, role)
            )
            conn.commit()
            return True, "Registration successful! Please login."
        except Error as e:
            return False, f"Error: {e}"
        finally:
            if conn.is_connected():
                conn.close()
    return False, "Could not connect to database"


def login_user(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT username, password, salt, role FROM USERS WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            if user and 'salt' in user and verify_password(user['password'], user['salt'], password):
                return user
            return None
        except Error as e:
            st.error(f"Database error: {e}")
            return None
        finally:
            if conn.is_connected():
                conn.close()
    return None



# Add this to Dashboard.py after the existing metrics section

def get_expiring_licenses():
    """Get licenses that are expired or expiring soon"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)

            # Get already expired licenses
            cursor.execute("""
                           SELECT l.license_id,
                                  c.customer_name,
                                  p.product_name,
                                  l.quantity,
                                  l.expiry_date,
                                  DATEDIFF(l.expiry_date, CURDATE()) as days_remaining
                           FROM licenses l
                                    JOIN customers c ON l.customer_id = c.customer_id
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.expiry_date < CURDATE()
                           ORDER BY l.expiry_date ASC
                           """)
            expired = cursor.fetchall()

            # Get licenses expiring within 21 days (3 weeks)
            cursor.execute("""
                           SELECT l.license_id,
                                  c.customer_name,
                                  p.product_name,
                                  l.quantity,
                                  l.expiry_date,
                                  DATEDIFF(l.expiry_date, CURDATE()) as days_remaining
                           FROM licenses l
                                    JOIN customers c ON l.customer_id = c.customer_id
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.expiry_date >= CURDATE()
                             AND l.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 21 DAY)
                           ORDER BY l.expiry_date ASC
                           """)
            expiring_soon = cursor.fetchall()

            return {
                'expired': expired,
                'expiring_soon': expiring_soon
            }

        except Error as e:
            st.error(f"Database error: {e}")
            return {'expired': [], 'expiring_soon': []}
        finally:
            if conn.is_connected():
                conn.close()
    return {'expired': [], 'expiring_soon': []}


def show_license_renewal_section():
    """Display tables for expired and soon-to-expire licenses"""
    st.markdown("---")
    st.subheader("License Renewal Status")

    licenses = get_expiring_licenses()

    # Expired licenses table
    with st.expander("⚠️ Expired Licenses (Needs Immediate Attention)", expanded=True):
        if licenses['expired']:
            expired_df = pd.DataFrame(licenses['expired'])
            expired_df['days_remaining'] = expired_df['days_remaining'].apply(lambda x: f"Expired {abs(x)} days ago")

            st.dataframe(
                expired_df,
                column_config={
                    "license_id": "License ID",
                    "customer_name": "Customer",
                    "product_name": "Product",
                    "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                    "expiry_date": st.column_config.DateColumn("Expiry Date"),
                    "days_remaining": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No expired licenses found!")

    # Expiring soon table
    with st.expander("🔔 Licenses Expiring Soon (Within 3 Weeks)", expanded=True):
        if licenses['expiring_soon']:
            expiring_df = pd.DataFrame(licenses['expiring_soon'])
            expiring_df['days_remaining'] = expiring_df['days_remaining'].apply(
                lambda x: f"Expires in {x} days" if x > 0 else "Expires today"
            )

            st.dataframe(
                expiring_df,
                column_config={
                    "license_id": "License ID",
                    "customer_name": "Customer",
                    "product_name": "Product",
                    "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                    "expiry_date": st.column_config.DateColumn("Expiry Date"),
                    "days_remaining": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No licenses expiring in the next 3 weeks!")

# --- MAIN APP ROUTER ---
def main():
    st.set_page_config(layout="wide")

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None

    # If not logged in, show login/signup
    if not st.session_state.logged_in:
        show_login()
        return

    # Navigation for logged-in users

    logo = "images/logo.png"
    st.logo(logo)

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "Dashboard",
        "Customer Master",
        "Product Master",
        "License Master",
        "Customer Product View",
        "Renewal Updates",
        "Request Form",
        "Admin Requests" if st.session_state.get('role') == 'admin' else None,
        "Settings"

    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"### Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    if page == "Dashboard":
        show_dashboard()
    elif page == "Customer Master":
        from CustomerMaster import show_customer_master
        show_customer_master()
    elif page == "Product Master":
        from ProductMaster import show_product_master
        show_product_master()
    elif page == "License Master":
        from LicenseEntry import show_license_entry
        show_license_entry()
    elif page == "Customer Product View":
        from CustomerProductView import show_customer_product_view
        show_customer_product_view()
    elif page == "Renewal Updates":
        from RenewalUpdates import show_renewal_updates
        show_renewal_updates()
    elif page == "Request Form":
        from RequestForm import show_request_form
        show_request_form()
    elif page == "Admin Requests":
        from AdminRequests import show_admin_requests
        show_admin_requests()
    elif page == "Settings":
        from Settings import show_settings
        show_settings()


def show_login():
    st.title("🔐 Corporate IT Solutions Login")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("Login Form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user['username']
                    st.session_state.role = user.get('role', 'user')  # Default to 'user' if role not found
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("Signup Form"):
            st.subheader("Create Account")
            new_user = st.text_input("Username*")
            new_email = st.text_input("Email*")
            new_pass = st.text_input("Password*", type="password")
            confirm_pass = st.text_input("Confirm Password*", type="password")

            # Only show role selection for admin users (if you want to restrict admin creation)
            if st.session_state.get('logged_in') and st.session_state.get('role') == 'admin':
                role = st.selectbox("Role", ["user", "admin"])
            else:
                role = "user"

            if st.form_submit_button("Register"):
                if not all([new_user, new_email, new_pass, confirm_pass]):
                    st.error("Please fill all required fields (*)")
                elif new_pass != confirm_pass:
                    st.error("Passwords don't match!")
                else:
                    success, message = register_user(new_user, new_email, new_pass, role)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)


if __name__ == "__main__":
    main()