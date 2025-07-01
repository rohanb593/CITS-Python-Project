# Settings.py

import streamlit as st
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

# --- Update password ---
def update_password(username, current_password, new_password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM USERS WHERE username = %s AND password = %s",
                (username, current_password)
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE USERS SET password = %s WHERE username = %s",
                    (new_password, username)
                )
                conn.commit()
                return True
            else:
                return False
        except Error as e:
            st.error(f"Error updating password: {e}")
            return False
        finally:
            conn.close()
    return None


# --- Delete account ---
def delete_account(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM USERS WHERE username = %s AND password = %s",
                (username, password)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            st.error(f"Error deleting account: {e}")
            return False
        finally:
            conn.close()
    return None


# --- MAIN SETTINGS PAGE ---
def show_settings():
    st.set_page_config(page_title="Settings", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("⚠️ Please log in to access settings.")
        st.markdown("[Back to Login](../app.py)")
        return

    username = st.session_state.username
    st.title("⚙️ Settings")


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
                success = update_password(username, current, new)
                if success:
                    st.success("Password updated successfully!")
                else:
                    st.error("Incorrect current password.")

    # --- Delete Account ---
    with st.expander("🗑️ Delete Account"):
        st.warning("This action is irreversible.")
        del_pass = st.text_input("Confirm your password to delete account", type="password")
        if st.button("Delete My Account"):
            if delete_account(username, del_pass):
                st.success("Your account has been deleted.")
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()
            else:
                st.error("Incorrect password or error deleting account.")



if __name__ == "__main__":
    show_settings()
