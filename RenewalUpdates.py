# RenewalUpdates.py
import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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


def get_expiring_licenses(days_threshold=21):
    """Get licenses that are expired or expiring soon"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)

            # Get already expired licenses
            cursor.execute("""
                           SELECT l.license_id,
                                  c.customer_name,
                                  c.email,
                                  p.product_name,
                                  l.quantity,
                                  l.expiry_date,
                                  CAST(DATEDIFF(l.expiry_date, CURDATE()) AS SIGNED) as days_remaining
                           FROM licenses l
                                    JOIN customers c ON l.customer_id = c.customer_id
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.expiry_date < CURDATE()
                           ORDER BY l.expiry_date ASC
                           """)
            expired = cursor.fetchall()

            # Get licenses expiring within specified days
            cursor.execute("""
                           SELECT l.license_id,
                                  c.customer_name,
                                  c.email,
                                  p.product_name,
                                  l.quantity,
                                  l.expiry_date,
                                  CAST(DATEDIFF(l.expiry_date, CURDATE()) AS SIGNED) as days_remaining
                           FROM licenses l
                                    JOIN customers c ON l.customer_id = c.customer_id
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.expiry_date >= CURDATE()
                             AND l.expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                           ORDER BY l.expiry_date ASC
                           """, (days_threshold,))
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


def send_email_notification(recipient_email, subject, message, smtp_config):
    """Send email notification using SMTP"""
    try:
        # Create message with explicit UTF-8 encoding
        msg = MIMEMultipart()
        msg['From'] = smtp_config['sender_email']
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html', 'utf-8'))  # ← Force UTF-8

        # Connect to SMTP server
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            server.ehlo()  # Identify to server
            if smtp_config['use_tls']:
                server.starttls()  # Enable TLS
                server.ehlo()
            # Ensure password is encoded properly
            password = smtp_config['smtp_password'].encode('utf-8').decode('ascii', 'ignore')
            server.login(smtp_config['smtp_username'], password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False


def get_email_template(license_data, notification_type):
    """Generate HTML email template based on license data and notification type"""
    if notification_type == "expired":
        subject = f"URGENT: License Renewal Required for {license_data['product_name']}"
        days_text = f"expired {abs(license_data['days_remaining'])} days ago"
        urgency = "immediate attention"
        action = "renew immediately"
    else:
        subject = f"Upcoming License Renewal for {license_data['product_name']}"
        days_text = f"expiring in {license_data['days_remaining']} days"
        urgency = "attention"
        action = "renew"

    html = f"""
    <html>
    <body>
        <p>Dear {license_data['customer_name']},</p>

        <p>This is a reminder that your license for <strong>{license_data['product_name']}</strong> 
        (Quantity: {license_data['quantity']}) is {days_text} (Expiry Date: {license_data['expiry_date'].strftime('%Y-%m-%d')}).</p>

        <p>Please {action} to avoid any disruption to your service. This requires your {urgency}.</p>

        <p>To proceed with the renewal, please contact our support team or reply to this email.</p>

        <p>Best regards,<br>
        Corporate IT Solutions Team</p>
    </body>
    </html>
    """

    return subject, html


def show_renewal_updates():
    st.set_page_config(page_title="Renewal Updates", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Renewal Notifications")
    st.markdown("Send renewal reminders to clients for expiring or expired licenses.")

    # SMTP Configuration Section
    with st.expander("📧 Email Server Configuration", expanded=True):
        st.info("Configure your SMTP email server settings to send notifications")

        # Initialize session state for SMTP config if not exists
        # In the show_renewal_updates() function, replace the SMTP config initialization with:
        if 'smtp_config' not in st.session_state:
            st.session_state.smtp_config = {
                'sender_email': 't0200795@gmail.com',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': 't0200795@gmail.com',
                'smtp_password': 'cwee omon xfbd kqwc',  # Paste the app password here
                'use_tls': True
            }

        # Form for SMTP configuration
        with st.form("smtp_config_form"):
            col1, col2 = st.columns(2)
            with col1:
                sender_email = st.text_input(
                    "Sender Email",
                    value=st.session_state.smtp_config['sender_email']
                )
                smtp_server = st.text_input(
                    "SMTP Server",
                    value=st.session_state.smtp_config['smtp_server']
                )
                smtp_port = st.number_input(
                    "SMTP Port",
                    min_value=1,
                    max_value=65535,
                    value=st.session_state.smtp_config['smtp_port']
                )
            with col2:
                smtp_username = st.text_input(
                    "SMTP Username",
                    value=st.session_state.smtp_config['smtp_username']
                )
                smtp_password = st.text_input(
                    "SMTP Password",
                    type="password",
                    value=st.session_state.smtp_config['smtp_password']
                )
                use_tls = st.checkbox(
                    "Use TLS",
                    value=st.session_state.smtp_config['use_tls']
                )

            if st.form_submit_button("Save SMTP Configuration"):
                st.session_state.smtp_config = {
                    'sender_email': sender_email,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'smtp_username': smtp_username,
                    'smtp_password': smtp_password,
                    'use_tls': use_tls
                }
                st.success("SMTP configuration saved!")

    # License Selection Section
    with st.expander("📝 Select Licenses for Notification", expanded=True):
        days_threshold = st.slider(
            "Show licenses expiring within (days):",
            min_value=1,
            max_value=90,
            value=21
        )

        licenses = get_expiring_licenses(days_threshold)

        # Expired licenses
        # Expired licenses
        if licenses['expired']:
            st.subheader("Expired Licenses (Needs Immediate Attention)")
            expired_df = pd.DataFrame(licenses['expired'])
            # Keep original days_remaining for calculations but add a display column
            expired_df['status_display'] = expired_df['days_remaining'].apply(lambda x: f"Expired {abs(x)} days ago")

            # Add checkbox column
            expired_df['Select'] = False
            edited_expired_df = st.data_editor(
                expired_df,
                column_config={
                    "license_id": "License ID",
                    "customer_name": "Customer",
                    "email": "Email",
                    "product_name": "Product",
                    "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                    "expiry_date": st.column_config.DateColumn("Expiry Date"),
                    "status_display": st.column_config.TextColumn("Status"),
                    "Select": st.column_config.CheckboxColumn("Select for Notification"),
                    "days_remaining": None  # Hide this column from display
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No expired licenses found")

        # Expiring soon licenses
        # Expiring soon licenses
        if licenses['expiring_soon']:
            st.subheader(f"Licenses Expiring Soon (Within {days_threshold} Days)")
            expiring_df = pd.DataFrame(licenses['expiring_soon'])
            # Keep original days_remaining for calculations but add a display column
            expiring_df['status_display'] = expiring_df['days_remaining'].apply(
                lambda x: f"Expires in {x} days" if x > 0 else "Expires today"
            )

            # Add checkbox column
            expiring_df['Select'] = False
            edited_expiring_df = st.data_editor(
                expiring_df,
                column_config={
                    "license_id": "License ID",
                    "customer_name": "Customer",
                    "email": "Email",
                    "product_name": "Product",
                    "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                    "expiry_date": st.column_config.DateColumn("Expiry Date"),
                    "status_display": st.column_config.TextColumn("Status"),
                    "Select": st.column_config.CheckboxColumn("Select for Notification"),
                    "days_remaining": None  # Hide this column from display
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"No licenses expiring in the next {days_threshold} days")

    # Notification Preview and Sending Section
    with st.expander("✉️ Compose and Send Notifications", expanded=True):
        st.subheader("Notification Preview")

        # Get selected licenses
        selected_licenses = []
        try:
            selected_expired = edited_expired_df[edited_expired_df['Select'] == True].to_dict('records')
            selected_licenses.extend(selected_expired)
        except:
            pass

        try:
            selected_expiring = edited_expiring_df[edited_expiring_df['Select'] == True].to_dict('records')
            selected_licenses.extend(selected_expiring)
        except:
            pass

        if not selected_licenses:
            st.warning("Please select at least one license to send notifications")
        else:
            # Show selected licenses
            st.write(f"Selected {len(selected_licenses)} licenses for notification:")
            selected_df = pd.DataFrame(selected_licenses)
            st.dataframe(selected_df[['customer_name', 'email', 'product_name', 'expiry_date']], hide_index=True)

            # Custom message option
            custom_message = st.text_area(
                "Additional Message (optional)",
                height=100,
                placeholder="Add any additional message to include in the notifications"
            )

            # Test email option
            test_email = st.text_input(
                "Send test email to (optional)",
                placeholder="Enter email address to send a test notification"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Send Test Notification") and test_email:
                    # Use the first selected license for test
                    test_license = selected_licenses[0]

                    notification_type = "expired" if int(test_license['days_remaining']) < 0 else "expiring"
                    subject, html_content = get_email_template(test_license, notification_type)

                    if custom_message:
                        html_content = html_content.replace(
                            "</body>",
                            f"<p><strong>Additional Note:</strong> {custom_message}</p></body>"
                        )

                    if send_email_notification(
                            test_email,
                            f"[TEST] {subject}",
                            html_content,
                            st.session_state.smtp_config
                    ):
                        st.success(f"Test notification sent to {test_email}")
                    else:
                        st.error("Failed to send test notification")

            with col2:
                if st.button("Send All Notifications", type="primary"):
                    progress_bar = st.progress(0)
                    success_count = 0
                    total = len(selected_licenses)

                    for i, license_data in enumerate(selected_licenses):
                        # In both test and bulk sending sections, ensure proper type conversion:
                        notification_type = "expired" if int(license_data['days_remaining']) < 0 else "expiring"
                        subject, html_content = get_email_template(license_data, notification_type)

                        if custom_message:
                            html_content = html_content.replace(
                                "</body>",
                                f"<p><strong>Additional Note:</strong> {custom_message}</p></body>"
                            )

                        if send_email_notification(
                                license_data['email'],
                                subject,
                                html_content,
                                st.session_state.smtp_config
                        ):
                            success_count += 1

                        progress_bar.progress((i + 1) / total)

                    st.success(f"Successfully sent {success_count} out of {total} notifications")

                    # Log the notification in the database
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            for license_data in selected_licenses:
                                cursor.execute("""
                                               INSERT INTO renewal_notifications
                                               (license_id, customer_id, product_id, notification_date,
                                                notification_type)
                                               SELECT l.license_id,
                                                      l.customer_id,
                                                      l.product_id,
                                                      NOW(),
                                                      %s
                                               FROM licenses l
                                               WHERE l.license_id = %s
                                               """, (
                                                   "expired" if license_data['days_remaining'] < 0 else "expiring",
                                                   license_data['license_id']
                                               ))
                            conn.commit()
                        except Error as e:
                            st.error(f"Error logging notifications: {e}")
                        finally:
                            if conn.is_connected():
                                conn.close()


if __name__ == "__main__":
    show_renewal_updates()