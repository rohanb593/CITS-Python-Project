# app.py

import streamlit as st
from altair.vega import title
from LicenseEntry import show_license_entry
from Dashboard import show_dashboard
import mysql.connector
from mysql.connector import Error


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


def register_user(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO USERS (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
            st.success("Registration successful! Please login.")
            return True
        except Error as e:
            st.error(f"Error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False


def login_user(username, password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM USERS WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()
        return user is not None
    return False


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
        "License Entry",
        "Customer Product View",
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
    elif page == "License Entry":
        from LicenseEntry import show_license_entry
        show_license_entry()
    elif page == "Customer Product View":
        from CustomerProductView import show_customer_product_view
        show_customer_product_view()
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
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("Signup Form"):
            st.subheader("Create Account")
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Register"):
                if new_pass != confirm_pass:
                    st.error("Passwords don't match!")
                elif username_exists(new_user):
                    st.error("Username already exists!")
                else:
                    if register_user(new_user, new_pass):
                        st.success("Account created! Switch to Login tab.")


if __name__ == "__main__":
    main()