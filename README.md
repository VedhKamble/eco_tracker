🌱 EcoTracker – Carbon Footprint & Sustainability Tracker

EcoTracker is a Python-based sustainability tracking application designed to help users calculate their daily carbon footprint, receive eco-friendly tips, and track progress toward sustainable living. The project focuses on simplifying carbon tracking by reducing complex inputs and providing a user-friendly interface.

🚀 Features Implemented

✅ User creation and management
✅ Daily carbon footprint calculation
✅ AI-powered eco tips using OpenAI API
✅ MySQL database integration
✅ Backend built with FastAPI
✅ Frontend built with Streamlit
✅ Modular and structured project design

🛠️ Tech Stack

1) Frontend: Streamlit
2) Backend: FastAPI
3) Database: MySQL
4) AI Integration: OpenAI API
5) Language: Python

⚠️ Current Project Status (Important)

Note: This project is currently partially complete.
Due to time constraints and parallel academic/internship commitments, the following issues are known and pending:
❌ Log entry data is not consistently being inserted into the logs table
❌ User statistics (points/streak) endpoint may return errors in some cases
❌ Frontend UI does not always display success/error messages correctly for all API calls
These issues are primarily related to API integration and frontend–backend synchronization, and not the overall project structure.

🗂️ Repository Structure
eco_tracker/
├── api_client.py          # API integrations (if any)
├── backend_main.py        # Main backend logic & routing
├── calculator.py          # Carbon calculation functions
├── frontend_app.py        # USer Interface logic
├── README.md             # This documentation


How It Works
1) calculator.py — Core logic computes carbon emissions based on input factors such as transportation, energy use, and habits.
2) api_client.py — Contains API handlers (placeholders for future integrations like real-time data).
3) backend_main.py — Orchestrates calculation flows and ties backend logic with UI.
4) frontend_app.py — Provides the user-facing interface to interact with.

Future Improvements:-

1) Fix log entry insertion logic
2) Stabilize user statistics retrieval
3) Improve frontend feedback and error handling
4) Add habit streak visualization
5) Refactor DB layer using ORM (SQLAlchemy)

📄 Disclaimer

This project was developed as part of a learning and internship-focused initiative. While core functionality is implemented, some features require further debugging and refinement. Contributions and improvements are welcome.

👤 Author

Vedh Kamble
Computer Science Student | Python Developer | Cybersecurity & AI Enthusiast
