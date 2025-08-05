# Settings.py

import streamlit as st
import mysql.connector
from mysql.connector import Error
import hashlib
import secrets


# --- Password Hashing Functions ---
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


# --- Update password ---
def update_password(username, current_password, new_password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # First get the user's current salt and hashed password
            cursor.execute(
                "SELECT password, salt FROM USERS WHERE username = %s",
                (username,)
            )
            user_data = cursor.fetchone()

            if not user_data:
                return False, "User not found"

            # Verify current password
            if not verify_password(user_data['password'], user_data['salt'], current_password):
                return False, "Incorrect current password"

            # Generate new salt and hash for the new password
            new_salt = generate_salt()
            new_hashed_password = hash_password(new_password, new_salt)

            # Update both password and salt in database
            cursor.execute(
                "UPDATE USERS SET password = %s, salt = %s WHERE username = %s",
                (new_hashed_password, new_salt, username)
            )
            conn.commit()
            return True, "Password updated successfully"
        except Error as e:
            return False, f"Error updating password: {e}"
        finally:
            conn.close()
    return False, "Could not connect to database"


# --- Check if username exists ---
def username_exists(username):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM USERS WHERE username = %s", (username,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Error as e:
            st.error(f"Database error: {e}")
            return True  # Assume exists to prevent duplicates on error
    return True  # Assume exists if connection fails


# --- Update username ---
# --- Update username ---
def update_username(current_username, new_username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # First verify current credentials by getting user data
            cursor.execute(
                "SELECT password, salt FROM USERS WHERE username = %s",
                (current_username,)
            )
            user_data = cursor.fetchone()

            if not user_data:
                return False, "User not found"

            # Verify password
            if not verify_password(user_data['password'], user_data['salt'], password):
                return False, "Incorrect current password"

            # Check if new username already exists
            if username_exists(new_username):
                return False, "Username already taken"

            # Update the username
            cursor.execute(
                "UPDATE USERS SET username = %s WHERE username = %s",
                (new_username, current_username)
            )
            conn.commit()
            return True, "Username updated successfully"
        except Error as e:
            return False, f"Database error: {e}"
        finally:
            conn.close()
    return False, "Could not connect to database"


# --- Delete account ---
def delete_account(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # First verify credentials
            cursor.execute(
                "SELECT password, salt FROM USERS WHERE username = %s",
                (username,)
            )
            user_data = cursor.fetchone()

            if not user_data:
                return False, "User not found"

            if not verify_password(user_data['password'], user_data['salt'], password):
                return False, "Incorrect password"

            # Delete the account
            cursor.execute(
                "DELETE FROM USERS WHERE username = %s",
                (username,)
            )
            conn.commit()
            return True, "Account deleted successfully"
        except Error as e:
            return False, f"Error deleting account: {e}"
        finally:
            conn.close()
    return False, "Could not connect to database"


# --- MAIN SETTINGS PAGE ---
def show_settings():
    st.set_page_config(page_title="Settings", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("⚠️ Please log in to access settings.")
        st.markdown("[Back to Login](../app.py)")
        return

    username = st.session_state.username
    st.title("⚙️ Settings")

    # --- Change Username ---
    # --- Change Username ---
    with st.expander("👤 Change Username"):
        current_username = st.text_input("Current Username", value=username, disabled=True)
        new_username = st.text_input("New Username")
        current_pass = st.text_input("Confirm Current Password", type="password")

        if st.button("Update Username"):
            if not new_username or not current_pass:
                st.warning("Please fill in all fields")
            elif new_username == username:
                st.warning("New username cannot be the same as current username")
            else:
                success, message = update_username(username, new_username, current_pass)
                if success:
                    st.success(message)
                    st.session_state.username = new_username
                    # Add a slight delay to make sure the message is visible
                    st.session_state.show_username_update_message = True
                    st.rerun()
                else:
                    st.error(message)

        # Show the success message after rerun if needed
        if st.session_state.get('show_username_update_message', False):
            st.success("Username updated successfully.")
            st.session_state.show_username_update_message = False

    # --- Change Password ---
    with st.expander("🔒 Change Password"):
        current = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")

        if st.button("Update Password"):
            if not current or not new or not confirm:
                st.warning("Please fill in all fields.")
            elif new != confirm:
                st.error("New passwords do not match.")
            else:
                success, message = update_password(username, current, new)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # --- Delete Account ---
    with st.expander("🗑️ Delete Account"):
        st.warning("This action is irreversible.")
        del_pass = st.text_input("Confirm your password to delete account", type="password")
        if st.button("Delete My Account"):
            success, message = delete_account(username, del_pass)
            if success:
                st.success(message)
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()
            else:
                st.error(message)


if __name__ == "__main__":
    show_settings()