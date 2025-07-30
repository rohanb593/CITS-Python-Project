# RequestForm.py
import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
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


def save_request(request_data):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                           INSERT INTO requests
                               (name, date, topic, description, status, created_at)
                           VALUES (%s, %s, %s, %s, %s, NOW())
                           """, request_data)
            conn.commit()
            return True
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False


def get_all_requests():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT request_id,
                                  name,
                                  DATE_FORMAT(date, '%%Y-%%m-%%d') as date,
                    topic,
                    description,
                    status,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as created_at
                           FROM requests
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


def update_request_status(request_id, new_status):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE requests
                           SET status = %s
                           WHERE request_id = %s
                           """, (new_status, request_id))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False


def show_request_form():
    st.set_page_config(page_title="Request Form", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Request Form")

    # Initialize session state
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'selected_request' not in st.session_state:
        st.session_state.selected_request = None

    # Toggle switch for edit mode (admin view)
    if st.session_state.username == "admin":  # Or your admin username
        edit_mode = st.toggle("Admin Mode", value=st.session_state.edit_mode, key="admin_toggle")
        if edit_mode != st.session_state.edit_mode:
            st.session_state.edit_mode = edit_mode
            st.rerun()

    # New request form
    with st.expander("➕ Submit New Request", expanded=True):
        with st.form("request_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Your Name*", max_chars=100)
                date = st.date_input("Date*", datetime.now())
            with col2:
                topic = st.text_input("Topic*", max_chars=100)
                status = "Pending"  # Default status for new requests

            description = st.text_area("Description*", max_chars=500,
                                       placeholder="Please describe your request in detail")

            submitted = st.form_submit_button("Submit Request")
            if submitted:
                if not all([name, topic, description]):
                    st.error("Please fill all required fields (*)")
                else:
                    request_data = (name, date, topic, description, status)
                    if save_request(request_data):
                        st.success("Request submitted successfully!")
                        st.rerun()
                    else:
                        st.error("Error submitting request")

    # View existing requests
    st.subheader("Request History")
    requests = get_all_requests()

    if requests:
        if st.session_state.edit_mode:  # Admin view with status management
            df = pd.DataFrame(requests)
            # Reorder columns for display
            df = df[['request_id', 'name', 'date', 'topic', 'description', 'status', 'created_at']]

            # Create editable dataframe for status
            edited_df = st.data_editor(
                df,
                column_config={
                    "request_id": "ID",
                    "name": "Name",
                    "date": "Date",
                    "topic": "Topic",
                    "description": "Description",
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Pending", "In Progress", "Completed", "Rejected"],
                        required=True
                    ),
                    "created_at": "Submitted On"
                },
                use_container_width=True,
                hide_index=True,
                key="request_editor"
            )

            # Save changes button
            if st.button("Save Changes"):
                # Check for changes
                for idx, row in edited_df.iterrows():
                    original_status = df.iloc[idx]['status']
                    new_status = row['status']

                    if original_status != new_status:
                        if update_request_status(row['request_id'], new_status):
                            st.success(f"Updated request ID {row['request_id']} status to {new_status}")
                        else:
                            st.error(f"Failed to update request ID {row['request_id']}")
                st.rerun()
        else:  # Regular user view
            user_requests = [r for r in requests if r['name'] == st.session_state.username]

            if user_requests:
                df = pd.DataFrame(user_requests)
                # Reorder columns for display
                df = df[['request_id', 'date', 'topic', 'description', 'status', 'created_at']]

                st.dataframe(
                    df,
                    column_config={
                        "request_id": "ID",
                        "date": "Date",
                        "topic": "Topic",
                        "description": "Description",
                        "status": "Status",
                        "created_at": "Submitted On"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("You haven't submitted any requests yet")
    else:
        st.info("No requests found in the system")


if __name__ == "__main__":
    show_request_form()