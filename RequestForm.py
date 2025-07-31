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
                               (name, date, topic, description, currency, amount, status, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, 'Pending', NOW())
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
                SELECT 
                    name,
                    date,
                    topic,
                    description,
                    currency,
                    amount,
                    status,
                    processed_by,
                    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as created_at,
                    DATE_FORMAT(processed_at, '%Y-%m-%d %H:%i') as processed_at
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



def update_request_status(request_id, new_status, processed_by=None):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if processed_by:
                cursor.execute("""
                               UPDATE requests
                               SET status       = %s,
                                   processed_by = %s,
                                   processed_at = NOW()
                               WHERE request_id = %s
                               """, (new_status, processed_by, request_id))
            else:
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

    # New request form
    with st.expander("➕ Submit New Request", expanded=True):
        with st.form("request_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Your Name*", max_chars=100, value=st.session_state.username)
                date = st.date_input("Date*", datetime.now())
            with col2:
                topic = st.text_input("Topic*", max_chars=100)
                currency = st.radio("Currency*", ["USD", "ZMW"], horizontal=True)

            amount = st.number_input("Amount*", min_value=0.0, step=0.01, format="%.2f")
            description = st.text_area("Description*", max_chars=500,
                                       placeholder="Please describe your request in detail")

            submitted = st.form_submit_button("Submit Request")
            if submitted:
                if not all([name, topic, description, amount > 0]):
                    st.error("Please fill all required fields (*) and ensure amount is positive")
                else:
                    request_data = (name, date, topic, description, currency, amount)
                    if save_request(request_data):
                        st.success("Request submitted successfully!")
                        st.rerun()
                    else:
                        st.error("Error submitting request")

    # View existing requests
    st.subheader("Your Request History")
    requests = get_all_requests()
    user_requests = [r for r in requests if r['name'] == st.session_state.username]

    if user_requests:
        df = pd.DataFrame(user_requests)
        # Format amount with currency
        df['amount'] = df.apply(lambda x: f"{x['currency']} {x['amount']:.2f}", axis=1)

        # Format date properly
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        st.dataframe(
            df[['date', 'topic', 'amount', 'description', 'status', 'created_at', 'processed_at']],
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "topic": "Topic",
                "amount": "Amount",
                "description": "Description",
                "status": st.column_config.TextColumn("Status"),
                "created_at": st.column_config.DatetimeColumn("Submitted On", format="YYYY-MM-DD HH:mm"),
                "processed_at": st.column_config.DatetimeColumn("Processed On", format="YYYY-MM-DD HH:mm")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("You haven't submitted any requests yet")


if __name__ == "__main__":
    show_request_form()