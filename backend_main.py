# backend/backend_main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import time
import openai
from calculator import calculate_carbon_for_entry

# Load OPENAI_API_KEY from env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

DB_PATH = os.getenv("ECOTRACKER_DB")

app = FastAPI(title="EcoTracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DB helpers (very small wrapper using sqlite3) ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        points INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        last_log_date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        travel_km REAL,
        travel_mode TEXT,
        electricity_kwh REAL,
        food TEXT,
        water_liters REAL,
        footprint_kg REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

init_db()

# --- Pydantic models ---
class Entry(BaseModel):
    name: str
    travel_km: float = 0.0
    travel_mode: Optional[str] = "car"   # car, bus, bike, walk
    electricity_kwh: float = 0.0
    food: Optional[str] = "veg"         # veg / non-veg
    water_liters: float = 0.0
    date: Optional[str] = None          # YYYY-MM-DD (optional)

class TipRequest(BaseModel):
    name: str
    footprint_kg: float
    focus_area: Optional[str] = None    # "transport", "electricity", "food", etc.

# --- Helper functions ---
def get_user(name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, points, streak, last_log_date FROM users WHERE name = ?", (name,))
    r = c.fetchone()
    conn.close()
    return r

def create_user(name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def add_log_and_update_user(name: str, entry: Entry, footprint: float):
    create_user(name)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, last_log_date, streak FROM users WHERE name = ?", (name,))
    user = c.fetchone()
    user_id = user[0]
    last_date = user[1]
    streak = user[2] or 0
    # Check if date is today to avoid double counting; simple logic:
    today = entry.date or time.strftime("%Y-%m-%d")
    if last_date != today:
        streak = streak + 1
    # insert log
    c.execute("""
    INSERT INTO logs (user_id, date, travel_km, travel_mode, electricity_kwh, food, water_liters, footprint_kg)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, today, entry.travel_km, entry.travel_mode, entry.electricity_kwh, entry.food, entry.water_liters, footprint))
    # update user points & streak & last_log_date
    points_gain = int(max(1, round(100 - footprint)))  # gamified; less footprint -> more points
    new_points = (get_user_points(name) or 0) + points_gain
    c.execute("UPDATE users SET points = ?, streak = ?, last_log_date = ? WHERE id = ?", (new_points, streak, today, user_id))
    conn.commit()
    conn.close()
    return {"points_gain": points_gain, "streak": streak, "points": new_points}

def get_user_points(name: str):
    r = get_user(name)
    if not r:
        return None
    return r[2]

# --- Routes ---
@app.post("/calculate_footprint")
def calculate_footprint(entry: Entry):
    try:
        footprint = calculate_carbon_for_entry(entry.dict())
        return {"footprint_kg": footprint}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/log_entry")
def log_entry(entry: Entry):
    try:
        footprint = calculate_carbon_for_entry(entry.dict())
        res = add_log_and_update_user(entry.name, entry, footprint)
        return {"footprint_kg": footprint, "points_gain": res["points_gain"], "streak": res["streak"], "points": res["points"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_tip")
def generate_tip(req: TipRequest):
    """
    Generate a personalized eco tip using OpenAI (if key available).
    If OPENAI_API_KEY not set, generate a rule-based fallback tip.
    """
    # Fallback rule-based tips
    fallback_tips = {
        "transport": "Consider switching short trips (<3 km) to walking or cycling. Use public transport where possible.",
        "electricity": "Turn off lights when not in use. Replace bulbs with LEDs and unplug idle chargers.",
        "food": "Choose plant-based meals more often; try 'meat-free Mondays'.",
        None: "Small daily actions add up. Track habits and aim to reduce one high-impact activity weekly."
    }
    if not OPENAI_API_KEY:
        return {"tip": fallback_tips.get(req.focus_area, fallback_tips[None])}
    # If OpenAI key available: call Chat Completion
    prompt = f"""
You are an empathetic eco-coach. The user {req.name} produced {req.footprint_kg:.2f} kg CO2 today.
Give one concise tip (2-3 short sentences) focused on {req.focus_area or 'general'} actions to reduce footprint tomorrow.
Include one measurable action and a simple reason.
"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini" if "gpt-4o-mini" in openai.Model.list() else "gpt-4o",
            messages=[{"role":"system","content":"You are a helpful eco coach."},{"role":"user","content":prompt}],
            max_tokens=120,
            temperature=0.6
        )
        text = resp["choices"][0]["message"]["content"].strip()
        return {"tip": text}
    except Exception as e:
        # fallback if OpenAI call fails
        return {"tip": fallback_tips.get(req.focus_area, fallback_tips[None]), "note": f"openai_error:{str(e)}"}

@app.get("/user_stats/{name}")
def user_stats(name: str):
    u = get_user(name)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = u[0]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT date, footprint_kg FROM logs WHERE user_id = ? ORDER BY date DESC LIMIT 30", (user_id,))
    logs = c.fetchall()
    conn.close()
    return {"name": u[1], "points": u[2], "streak": u[3], "logs": [{"date": d, "footprint_kg": f} for d,f in logs]}
