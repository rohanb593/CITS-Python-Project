import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd


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


def get_pending_requests():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT request_id,
                                  name,
                                  DATE_FORMAT(date, '%%Y-%%m-%%d') as date, 
                       topic, description, 
                       DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as created_at
                           FROM requests
                           WHERE status = 'Pending'
                           ORDER BY created_at DESC
                           """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []


def update_request_status(request_id, status, admin_username):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE requests
                           SET status       = %s,
                               processed_by = %s,
                               processed_at = NOW()
                           WHERE request_id = %s
                           """, (status, admin_username, request_id))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False


def show_admin_requests():
    st.set_page_config(page_title="Admin Requests", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    if st.session_state.get('role') != 'admin':
        st.error("You don't have permission to access this page.")
        return

    st.title("Admin Request Management")
    st.markdown("Review and process pending requests")

    requests = get_pending_requests()

    if requests:
        for req in requests:
            with st.expander(f"Request #{req['request_id']} - {req['topic']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Requester:** {req['name']}")
                    st.write(f"**Date:** {req['date']}")
                    st.write(f"**Submitted:** {req['created_at']}")
                with col2:
                    st.write(f"**Topic:** {req['topic']}")

                st.write("**Description:**")
                st.write(req['description'])

                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button(f"Approve", key=f"approve_{req['request_id']}"):
                        if update_request_status(req['request_id'], "Approved", st.session_state.username):
                            st.success("Request approved!")
                            st.rerun()
                        else:
                            st.error("Failed to update request")
                with col2:
                    if st.button(f"Reject", key=f"reject_{req['request_id']}"):
                        if update_request_status(req['request_id'], "Rejected", st.session_state.username):
                            st.success("Request rejected!")
                            st.rerun()
                        else:
                            st.error("Failed to update request")
    else:
        st.info("No pending requests found")


if __name__ == "__main__":
    show_admin_requests()