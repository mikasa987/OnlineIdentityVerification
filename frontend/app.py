import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Backend API URL
API_URL = "http://backend:8000"  # Docker service name

st.set_page_config(page_title="PakID Identity Verification", layout="wide")
st.title("PakID Identity Verification System")

# User Management Section
st.header("User Management")

# Create User
with st.expander("Add New User"):
    with st.form("user_form"):
        name = st.text_input("Full Name")
        cnic = st.text_input("CNIC Number")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if not all([name, cnic, phone, email]):
                st.error("All fields are required!")
            else:
                user_data = {
                    "name": name,
                    "cnic": cnic,
                    "phone": phone,
                    "email": email
                }
                try:
                    response = requests.post(f"{API_URL}/users/", json=user_data)
                    if response.status_code == 200:
                        st.success("User created successfully!")
                    else:
                        st.error(f"Error creating user: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")

# View Users
with st.expander("View All Users"):
    try:
        users_response = requests.get(f"{API_URL}/users/")
        if users_response.status_code == 200:
            users_df = pd.DataFrame(users_response.json())
            if not users_df.empty:
                st.dataframe(users_df, use_container_width=True)
            else:
                st.info("No users found")
        else:
            st.error(f"Error fetching users: {users_response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")

# Verification Requests Section
st.header("Verification Requests")

# Create Verification Request
with st.expander("Create New Verification Request"):
    with st.form("verification_form"):
        user_id = st.number_input("User ID", min_value=1)
        status = st.selectbox("Status", ["Pending", "Verified", "Rejected"])
        verification_method = st.selectbox("Verification Method",
                                           ["Biometric", "SMS OTP", "Email OTP", "Manual"])
        verified_by = st.text_input("Verified By (Agent ID/System)")
        submitted = st.form_submit_button("Submit Verification")

        if submitted:
            verification_data = {
                "user_id": user_id,
                "status": status,
                "verification_method": verification_method,
                "verified_by": verified_by
            }
            try:
                response = requests.post(f"{API_URL}/verifications/", json=verification_data)
                if response.status_code == 200:
                    st.success("Verification request created successfully!")
                else:
                    st.error(f"Error creating verification: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")

# View Verification Requests
with st.expander("View All Verification Requests"):
    try:
        verifications_response = requests.get(f"{API_URL}/verifications/")
        if verifications_response.status_code == 200:
            verifications_df = pd.DataFrame(verifications_response.json())
            if not verifications_df.empty:
                # Convert datetime strings to datetime objects
                verifications_df['request_date'] = pd.to_datetime(verifications_df['request_date'])
                # Format for display
                verifications_df['request_date'] = verifications_df['request_date'].dt.strftime('%Y-%m-%d %H:%M:%S')

                # Add filtering options
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.multiselect(
                        "Filter by Status",
                        options=verifications_df['status'].unique(),
                        default=verifications_df['status'].unique()
                    )
                with col2:
                    method_filter = st.multiselect(
                        "Filter by Method",
                        options=verifications_df['verification_method'].unique(),
                        default=verifications_df['verification_method'].unique()
                    )

                # Apply filters
                filtered_df = verifications_df[
                    (verifications_df['status'].isin(status_filter)) &
                    (verifications_df['verification_method'].isin(method_filter))
                    ]

                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.info("No verification requests found")
        else:
            st.error(f"Error fetching verifications: {verifications_response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")

# Update/Delete Section
st.header("Record Management")

# Update User
with st.expander("Update User"):
    user_id_to_update = st.number_input("User ID to Update", min_value=1, key="update_user_id")
    if st.button("Fetch User Details"):
        try:
            response = requests.get(f"{API_URL}/users/{user_id_to_update}")
            if response.status_code == 200:
                user_data = response.json()
                with st.form("update_user_form"):
                    name = st.text_input("Full Name", value=user_data["name"])
                    cnic = st.text_input("CNIC Number", value=user_data["cnic"])
                    phone = st.text_input("Phone Number", value=user_data["phone"])
                    email = st.text_input("Email Address", value=user_data["email"])
                    submitted = st.form_submit_button("Update User")

                    if submitted:
                        update_data = {
                            "name": name,
                            "cnic": cnic,
                            "phone": phone,
                            "email": email
                        }
                        update_response = requests.put(
                            f"{API_URL}/users/{user_id_to_update}",
                            json=update_data
                        )
                        if update_response.status_code == 200:
                            st.success("User updated successfully!")
                        else:
                            st.error(f"Error updating user: {update_response.text}")
            else:
                st.error(f"User not found: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")

# Delete User
with st.expander("Delete User"):
    user_id_to_delete = st.number_input("User ID to Delete", min_value=1, key="delete_user_id")
    if st.button("Delete User"):
        try:
            response = requests.delete(f"{API_URL}/users/{user_id_to_delete}")
            if response.status_code == 200:
                st.success("User deleted successfully!")
            else:
                st.error(f"Error deleting user: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")