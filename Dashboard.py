# Dashboard.py
import mysql
import streamlit as st
import pandas as pd
from datetime import datetime
from mysql.connector import Error

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

def get_customer_count():
    """Get total number of customers"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            return cursor.fetchone()[0]
        except Error as e:
            st.error(f"Database error: {e}")
            return 0
        finally:
            if conn.is_connected():
                conn.close()
    return 0


def get_license_stats():
    """Get active and expired license counts"""
    conn = get_db_connection()
    if conn:
        try:
            query = """
                    SELECT SUM(CASE WHEN expiry_date >= CURDATE() THEN 1 ELSE 0 END) as active, \
                           SUM(CASE WHEN expiry_date < CURDATE() THEN 1 ELSE 0 END)  as expired
                    FROM licenses \
                    """
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            st.error(f"Database error: {e}")
            return {'active': 0, 'expired': 0}
        finally:
            if conn.is_connected():
                conn.close()
    return {'active': 0, 'expired': 0}


def show_dashboard():
    st.set_page_config(page_title="Dashboard", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Corporate IT Solutions Dashboard")
    st.markdown("---")



    # Get data

    total_customers = int(get_customer_count())

    license_stats_raw = get_license_stats()
    license_stats = {
        'active': int(license_stats_raw['active']),
        'expired': int(license_stats_raw['expired']),
    }

    # Create metrics columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Customers",
            value=total_customers,
            delta="View all customers",
            help="Total number of customers"

        )

    with col2:
        st.metric(
            label="Active Licenses",
            value=license_stats['active'],
            delta="See details",
            help="Licenses currently in use"
        )

    with col3:
        st.metric(
            label="Expired Licenses",
            value=license_stats['expired'],
            delta="Needs attention",
            delta_color="inverse",
            help="Licenses requiring renewal"
        )

    # ===== LICENSE STATUS VISUALIZATION =====
    st.markdown("---")
    st.header("📈 License Status Overview")

    # Create a simple pie chart
    license_data = pd.DataFrame({
        'Status': ['Active', 'Expired'],
        'Count': [license_stats['active'], license_stats['expired']]
    })

    st.bar_chart(license_data.set_index('Status'))

    # ===== RECENT ACTIVITY SECTION =====
    st.markdown("---")
    st.header("🔄 Recent Activity")

    # Placeholder for recent activity - replace with real data
    st.write("""
    - **5** new licenses added this week
    - **3** renewals completed
    - **2** customer onboarding sessions
    """)


if __name__ == "__main__":
    show_dashboard()


