# frontend/frontend_app.py
import streamlit as st
import requests
import os
from dotenv import load_dotenv


load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
port = os.getenv("STREAMLIT_SERVER_PORT", 8501)


#--- Streamlit UI setup ---
st.set_page_config(page_title="EcoTracker", layout="centered")

st.markdown("<h1 style='text-align:center'>🌱 EcoTracker</h1> \
            <style>.stApp {background-img:url('frontend_bg_img.jpg'); \
            background-size:cover;}</style>", unsafe_allow_html=True)
st.markdown("", unsafe_allow_html=True)
st.write("A quick carbon footprint estimator + personalized tips")

#--- Create User ---
st.header("Create User")
with st.form("Create User Form"):
    nid = st.text_input("User ID", value="123")
    new_user = st.text_input("Enter your name", value = "Guest")
    submit_button = st.form_submit_button("Create User")
    if submit_button:
        resp = requests.post (f"{backend_url}/create_user", json={"id":nid,"name": new_user})
        if resp.status_code == 200:
            st.success(f"User '{new_user}' created successfully!")

 #--- AI Tips option ---

use_ai = False
st.subheader("AI Tips:")
if st.button("Use ChatGPT for personalized tips."):
    use_ai = True


# -- Input form
with st.form("daily_form"):
    name = st.text_input("Your name", value="Guest")
    st.subheader("Transport")
    col1, col2 = st.columns(2)
    with col1:
        travel_mode = st.selectbox("Mode", ["car", "bus", "bike", "walk"])
    with col2:
        travel_km = st.number_input("Distance (km)", min_value=0.0, step=0.5, value=0.0)
    st.subheader("Home")
    electricity_kwh = st.number_input("Electricity used today (kWh)", min_value=0.0, step=0.1, value=0.0)
    st.subheader("Food & Water")
    food = st.selectbox("Today's main meal", ["veg", "non-veg"])
    water_liters = st.number_input("Water used (liters)", min_value=0.0, step=0.5, value=0.0)
    submitted = st.form_submit_button("Calculate Footprint")


if submitted:
    payload = {
        "name": name,
        "travel_km": travel_km,
        "travel_mode": travel_mode,
        "electricity_kwh": electricity_kwh,
        "food": food,
        "water_liters": water_liters
    }
    resp = requests.post(f"{backend_url}/calculate_footprint", json=payload, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        footprint = data["footprint_kg"]
        st.success(f"Estimated footprint today: **{footprint} kg CO₂**")
        st.write("Quick suggestions:")

        # show small heuristic tips
        if travel_mode in ["car"] and travel_km > 2:
            st.info("Try public transport or carpooling for short trips.")
        if electricity_kwh > 5:
            st.info("Consider turning off unused appliances & using LED bulbs.")
        if food == "non-veg":
            st.info("Replace one meal with plant-based options to lower footprint.")

        # Generate AI tip
        tip_data = {
            "name": name,
            "footprint_kg": footprint,
            "focus_area": None,
            "use_ai": use_ai
        }
        tip_resp = requests.post(f"{backend_url}/generate_tip", json=tip_data, timeout=20)
        if tip_resp.status_code == 200:
            tip = tip_resp.json().get("tip")
            st.write(tip)

        # Option to log
        if st.button("Log today & earn points"):
            log_resp = requests.post(f"{backend_url}/log_entry", json={
        "name": name,
        "travel_km": travel_km,
        "travel_mode": travel_mode,
        "electricity_kwh": electricity_kwh,
        "food": food,
        "water_liters": water_liters
        }, timeout=20)
            if log_resp.status_code == 200:
                out = log_resp.json()
                st.success(f"Logged! +{out['points_gain']} points — Total points: {out['points']} — Streak: {out['streak']}")
            else:
                st.error("Could not log entry.")
    else:
        st.error("Error calculating footprint. Backend unreachable.")

#--- Show User Stats ---
st.header("User Stats")
user_name = st.text_input("Enter user name to view stats", value="Guest", key="stats_name")
if st.button("Get Stats"):
    resp = requests.post(f"{backend_url}/get_user_stats", json={"name": user_name})
    if resp.status_code == 200:
        stats = resp.json()
        st.write(f"Name: {stats['name']}")
        st.write(f"Total Points: {stats['points']}")
        st.write(f"Current Streak: {stats['streak']} days")
        st.write(f"Log Records: {stats['logs']}")
    else:
        st.error("User not found.")
    
