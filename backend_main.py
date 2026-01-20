# backend/backend_main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from backend.calculator import calculate_carbon_for_entry
from database.eco_tracker_db import create_connection

load_dotenv()

#--- Loading OpenAI API Key ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

#--- FastAPI app setup --   
app = FastAPI(title="EcoTracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models ---
class username(BaseModel):
    id: int
    name: str

class Entry(BaseModel):
    name: str
    travel_km: float = 0.0
    travel_mode: Optional[str] = "car"   # car, bus, bike, walk
    electricity_kwh: float = 0.0
    food: Optional[str] = "veg"         # veg / non-veg
    water_lts: float = 0.0
    date: Optional[str] = None          # YYYY-MM-DD (optional)

class TipRequest(BaseModel):
    name: str
    footprint_kg: float
    focus_area: Optional[str] = None    # "transport", "electricity", "food", etc.
    use_ai: bool = False                # whether to use AI for tip generation

# --- User Create & Fetch User functions ---
def create_user(id,name):
    conn = create_connection(db=True)
    if not conn:
        raise Exception("Database connection failed")
    mycur = conn.cursor()
    mycur.execute("INSERT INTO users (id,name) VALUES (%s,%s)", (id,name,))
    print("User created successfully.")
    conn.commit()
    conn.close()
def get_user(name):
    conn = create_connection(db=True)
    mycur = conn.cursor()
    mycur.execute("SELECT id, name, points, streak, last_log_date FROM users WHERE name = %s", (name,))
    user = mycur.fetchone()
    conn.commit()
    conn.close()
    return user



#--- Log Entry & Update User Stats ---
def add_log_and_update_user(name: str, entry: Entry, footprint: float):
    conn = create_connection(db= True)
    mycur = conn.cursor()

    mycur.execute("SELECT id, last_log_date, streak FROM users WHERE name = %s", (name,))
    user = mycur.fetchone()
    if not user:
        conn.close()
        raise Exception("User not found")
    
    user_id, streak = user[0], user[2]
    today = entry.date or time.strftime("%Y-%m-%d")

    #-- Prevent duplicate logs for same day --
    mycur.execute("SELECT COUNT(*) FROM logs WHERE user_id = %s AND date = %s", (user_id, today))
    already_logged = mycur.fetchone()[0]
    if already_logged > 0:
        streak = streak           # unchanged
        return "You already logged once!!!"  
    else:
        streak += 1

    #-- Insert Log Data of User --
    mycur.execute("""
    INSERT INTO logs (user_id, date, travel_km, travel_mode, electricity_kwh, food, water_lts, footprint_kg)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
    (user_id, today, entry.travel_km, entry.travel_mode, entry.electricity_kwh, entry.food, entry.water_lts, footprint))
    print("User log entry added successfully.")

    # -- Update user points, streak & last_log_date --
    points_gain = int(max(1, round(100 - footprint)))  # gamified; less footprint -> more points
    mycur.execute("SELECT points FROM users WHERE id = %s", (user_id,))
    current_points = mycur.fetchone()[0]
    new_points = current_points + points_gain
    mycur.execute("UPDATE users SET points = %s, streak = %s, last_log_date = %s WHERE id = %s", (new_points, streak, today, user_id))
    points = {"points_gain": points_gain, "streak": streak, "points": new_points}
    conn.commit()
    conn.close()
    return points

'''def get_user_points(name: str):
    usr = get_user(name)
    if not usr:
        return None
    return usr[2]'''

# --- Routes ---
@app.post("/create_user")
def new_user(user: username):
    try:
        create_user(user.id,user.name)
        return {"message": f"User '{user.name}' created successfully."}
    except Exception as e:
        print("CREATE USER ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

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
    if req.use_ai and client:
        # If OpenAI key available: call Chat Completion
        prompt = f"""
    You are an empathetic eco-coach. The user {req.name} produced {req.footprint_kg:.2f} kg CO2 today.
    Give one concise tip (2-3 short sentences) focused on {req.focus_area or 'general'} actions to reduce footprint tomorrow.
    Include one measurable action and a simple reason.
    """
        try:
            model_name="gpt-4o-mini"
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role":"system","content":"You are a helpful eco coach."},
                {"role":"user","content":prompt}],
                max_tokens=120,
                temperature=0.6
            )
            text = resp["choices"][0]["message"]["content"].strip()
            return {"tip": text}
        except Exception as e:
            return {"note": f"openai_error:{str(e)}"}
    else:
        # fallback if OpenAI call fails
        return {"tip": fallback_tips.get(req.focus_area, fallback_tips[None])}
    

@app.get("/get_user_stats")
def user_stats(name: dict):
    conn = create_connection(db= True)
    mycur = conn.cursor()
    u = get_user(name)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = u[0]
    mycur.execute("SELECT date, footprint_kg FROM logs WHERE user_id = %s ORDER BY date DESC LIMIT 30", (user_id,))
    logs = mycur.fetchall()
    conn.commit()
    conn.close()
    return {"name": u[1], "points": u[2], "streak": u[3], "logs": [{"date": d, "footprint_kg": f} for d,f in logs]}
