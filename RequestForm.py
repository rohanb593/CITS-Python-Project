import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_db_connection():
    """Establish connection to the database"""
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


def get_admin_emails():
    """Retrieve email addresses of all admin users"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT email FROM USERS WHERE role = 'admin'")
            return [row['email'] for row in cursor.fetchall()]
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []


def send_email_notification(recipients, subject, message):
    """Send email notification using SMTP"""
    try:
        # SMTP configuration (should be in your Streamlit secrets)
        smtp_config = {
            'sender_email': st.secrets.smtp.sender_email,
            'smtp_server': st.secrets.smtp.server,
            'smtp_port': st.secrets.smtp.port,
            'smtp_username': st.secrets.smtp.username,
            'smtp_password': st.secrets.smtp.password,
            'use_tls': st.secrets.smtp.use_tls
        }

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = smtp_config['sender_email']
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html', 'utf-8'))

        # Connect to SMTP server and send
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            server.ehlo()
            if smtp_config['use_tls']:
                server.starttls()
                server.ehlo()
            server.login(smtp_config['smtp_username'], smtp_config['smtp_password'])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False


def send_request_notification(request_data):
    """Send notification to admins about new request"""
    admin_emails = get_admin_emails()
    if not admin_emails:
        st.error("No admin emails found for notification")
        return False

    subject = f"New Request Submitted: {request_data[2]}"
    message = f"""
    <html>
    <body>
        <h3>New Request Notification</h3>
        <p>A new request has been submitted by {request_data[0]}:</p>

        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Field</th>
                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Value</th>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Requester</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{request_data[0]}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Date</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{request_data[1]}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Topic</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{request_data[2]}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Description</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{request_data[3]}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><strong>Amount</strong></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{request_data[5]} {request_data[4]}</td>
            </tr>
        </table>

        <p style="margin-top: 20px;">Please review this request in the admin panel.</p>

        <p>Best regards,<br>
        Corporate IT Solutions System</p>
    </body>
    </html>
    """

    return send_email_notification(admin_emails, subject, message)


def save_request(request_data):
    """Save new request to database and notify admins"""
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

            # Send notification after successful save
            send_request_notification(request_data)

            return True
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False


def get_all_requests():
    """Retrieve all requests from database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT name, date, topic, description, currency, amount, status, processed_by, DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as created_at, DATE_FORMAT(processed_at, '%Y-%m-%d %H:%i') as processed_at
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
    """Update status of a request"""
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
    """Main function to display the request form"""
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
                        st.success("Request submitted successfully! Admins have been notified.")
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
        # Format date
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