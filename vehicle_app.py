import streamlit as st
import pandas as pd
import bcrypt
import smtplib
from email.mime.text import MIMEText
import io

# --- Background Styling ---
import base64

def apply_custom_background_local(image_path: str):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
            background-repeat: no-repeat;
            background-position: center;
            color: black;
        }}
        .stTextInput > div > div > input {{
            background-color: #fce9d9;
            color: White;
        }}
        .stButton button {{
            background-color: #ed872d;
            color: white;
            border-radius: 10px;
            padding: 0.5em 1.5em;
        }}
        </style>
    """, unsafe_allow_html=True)



# --- Constants ---
SENDER_EMAIL = "yourcompany@example.com"
EMAIL_PASSWORD = "your-app-password"
USER_CSV = "users.csv"
VEHICLE_CSV = "vehicle_trip_data_synced.csv"

# --- Check Dependencies ---
try:
    import openpyxl
except ImportError:
    st.error("❌ Required package 'openpyxl' is not installed. Run `pip install openpyxl`.")
    st.stop()

# --- Load Data ---
try:
    users = pd.read_csv(USER_CSV)
except FileNotFoundError:
    users = pd.DataFrame(columns=["username", "name", "email", "password"])
    users.to_csv(USER_CSV, index=False)

def load_vehicles():
    try:
        return pd.read_csv(VEHICLE_CSV)
    except FileNotFoundError:
        st.error(f"Vehicle data file not found at {VEHICLE_CSV}")
        st.stop()

vehicles = load_vehicles()

# --- Utilities ---
def save_users():
    users.to_csv(USER_CSV, index=False)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def send_reset_email(to_email, username, temp_password):
    msg = MIMEText(f"Hi {username}, your temporary password is: {temp_password}")
    msg["Subject"] = "Temporary Password"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)

# --- Session ---
if "page" not in st.session_state:
    st.session_state.page = "login"

if "user" not in st.session_state:
    st.session_state.user = None

# --- Page 1: Login ---
if st.session_state.page == "login":
    apply_custom_background_local("page1.jpg")
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = users[users["username"] == username]
        if not user.empty and check_password(password, user.iloc[0]["password"]):
            st.session_state.user = username
            st.session_state.page = "lookup"
            st.success("Login successful!")
            st.stop()
        else:
            st.error("Invalid username or password.")

# --- Page 2: Vehicle Lookup ---
elif st.session_state.page == "lookup":
    apply_custom_background_local("page2.jpg")
    st.title("🚗 Vehicle Lookup")
    st.image("Set maker.png", width=150)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Back to Login"):
            st.session_state.page = "login"
            st.session_state.user = None
            st.stop()

    with col2:
        if st.button("Logout"):
            st.session_state.page = "login"
            st.session_state.user = None
            st.success("Logged out successfully!")
            st.stop()

    st.markdown("### 🔍 Search Vehicle by Number")
    vehicle_number_input = st.text_input("Enter Vehicle Number")

    uploaded_file = st.file_uploader("📤 Upload updated vehicle data (CSV)", type=["csv"])
    if uploaded_file is not None:
        vehicles = pd.read_csv(uploaded_file)
        vehicles.to_csv(VEHICLE_CSV, index=False)
        st.success("✅ Vehicle data updated successfully!")

    if st.button("Search"):
        vehicles = load_vehicles()  # Reload after upload
        if vehicle_number_input.strip() == "":
            st.warning("Please enter a vehicle number.")
        else:
            matched = vehicles[vehicles['Vehicle Number'].astype(str).str.contains(vehicle_number_input.strip(), case=False, na=False)]

            if not matched.empty:
                vehicle = matched.iloc[0]
                st.markdown(f"""
                <div style="background-color: #1e1e1e; padding: 1.5rem; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.4); color: white; font-family: 'Segoe UI'; width: 60%; margin: auto;">
                    <h3 style="color: #4FC3F7;">🚘 Vehicle Details</h3>
                    <hr style="border: 1px solid #444;">
                    <p><strong>Vehicle Number:</strong> {vehicle.get('Vehicle Number', 'N/A')}</p>
                    <p><strong>Registration Year:</strong> {vehicle.get('Registration Year', 'N/A')}</p>
                    <p><strong>FC Validity:</strong> {vehicle.get('FC Validity', 'N/A')}</p>
                    <p><strong>Service Required Every (KM):</strong> {vehicle.get('Service Required Every (KM)', 'N/A')}</p>
                    <p><strong>Container Type:</strong> {vehicle.get('Container Type', 'N/A')}</p>
                    <p><strong>Container:</strong> {vehicle.get('Container', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("No matching vehicle number found.")

    if st.button("✏️ Edit Vehicle Data"):
        st.session_state.page = "edit"
        st.stop()

# --- Page 3: Edit Vehicle Data ---
elif st.session_state.page == "edit":
    apply_custom_background_local("page3.jpg")
    st.title("🛠️ Edit Vehicle Data")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Back to Lookup"):
            st.session_state.page = "lookup"
            st.stop()
    with col2:
        if st.button("Logout"):
            st.session_state.page = "login"
            st.session_state.user = None
            st.success("Logged out successfully!")
            st.stop()

    if "original_vehicles" not in st.session_state:
        st.session_state.original_vehicles = vehicles.copy()

    st.subheader("Edit All Vehicle Records")

    with st.expander("🔍 Filter Options"):
        search_text = st.text_input("Search Vehicle Number")
        selected_columns = st.multiselect("Columns to Display", vehicles.columns.tolist(), default=vehicles.columns.tolist())

    vehicles = load_vehicles()
    filtered_data = vehicles.copy()
    if search_text:
        filtered_data = filtered_data[filtered_data['Vehicle Number'].astype(str).str.contains(search_text, case=False, na=False)]
    filtered_data = filtered_data[selected_columns]

    edited_data = st.data_editor(
        filtered_data,
        use_container_width=True,
        num_rows="dynamic",
        key="vehicle_editor",
        column_order=selected_columns,
        disabled=False
    )

    if st.button("💾 Save Changes"):
        vehicles.update(edited_data)
        vehicles.to_csv(VEHICLE_CSV, index=False)
        st.session_state.original_vehicles = vehicles.copy()
        st.success("All changes saved successfully!")

    if st.button("↩️ Undo Changes"):
        vehicles = st.session_state.original_vehicles.copy()
        st.success("Reverted to last saved version.")

    buffer = io.BytesIO()
    vehicles.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    st.download_button("📥 Download Excel", data=buffer, file_name="vehicle_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



















