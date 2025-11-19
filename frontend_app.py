# frontend/frontend_app.py
import streamlit as st
import requests
import os
from api_client import backend_url

st.set_page_config(page_title="EcoTracker", layout="centered")

st.markdown("<h1 style='text-align:center'>🌱 EcoTracker</h1> \
            <style>.stApp {background-img:url('frontend_bg_img.jpg'); \
            background-size:cover;}</style>", unsafe_allow_html=True)
st.markdown("", unsafe_allow_html=True)
st.write("A quick carbon footprint estimator + personalized tips")

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
        tip_resp = requests.post(f"{backend_url}/generate_tip", json={"name": name, "footprint_kg": footprint, "focus_area": None})
        if tip_resp.status_code == 200:
            tip = tip_resp.json().get("tip")
            st.write("**AI Tip:**")
            st.write(tip)
        # Option to log
        if st.button("Log today & earn points"):
            log_resp = requests.post(f"{backend_url}/log_entry", json=payload)
            if log_resp.status_code == 200:
                out = log_resp.json()
                st.success(f"Logged! +{out['points_gain']} points — Total points: {out['points']} — Streak: {out['streak']}")
            else:
                st.error("Could not log entry.")
    else:
        st.error("Error calculating footprint. Backend unreachable.")
