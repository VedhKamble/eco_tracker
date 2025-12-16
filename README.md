eco_tracker

A simple carbon calculator & habit tracker project built in Python — designed to help users estimate their carbon emissions with minimal input, learn actionable insights, and start sustainable habits.

🚀 Overview
eco_tracker is a lightweight Python-based tool that calculates carbon emissions based on user inputs and helps visualize sustainability impact. The project includes both backend logic and a basic frontend interface so users can interactively calculate and track their carbon footprint.

🔍 Features
🌱 Minimal input carbon footprint calculator
📊 Clean, intuitive frontend interface
🔁 Easy customization for new carbon categories
🔌 Modular Python structure (calculator.py, api_client.py, backend_main.py, frontend_app.py)
✨ Designed for expandability (habit tracking, daily nudges, personalized tips)

🗂️ Repository Structure
eco_tracker/
├── api_client.py          # API integrations (if any)
├── backend_main.py        # Main backend logic & routing
├── calculator.py          # Carbon calculation functions
├── frontend_app.py        # Frontend interface logic
├── README.md             # This documentation

Installation

1) Clone the repo
   git clone https://github.com/VedhKamble/eco_tracker.git
   cd eco_tracker
   
2) Create a Python virtual environment
   python3 -m venv env
   source env/bin/activate  # (Windows: env\Scripts\activate)
   
3) Install dependencies
   pip install -r requirements.txt

 Usage
1) Run the calculator
   python backend_main.py
   Follow prompts or open the local interface (if GUI/CLI menu implemented via frontend_app.py).

2) Run the frontend interface
   python frontend_app.py

How It Works
1) calculator.py — Core logic computes carbon emissions based on input factors such as transportation, energy use, and habits.
2) api_client.py — Contains API handlers (placeholders for future integrations like real-time data).
3) backend_main.py — Orchestrates calculation flows and ties backend logic with UI.
4) frontend_app.py — Provides the user-facing interface to interact with.

Future Plans
1) Add daily habit tracking and reminders
2) Track weekly/monthly carbon trends
3) Export reports (CSV/PDF)
4) Mobile-friendly UI or web dashboard
