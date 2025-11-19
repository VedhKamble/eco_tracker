# backend/calculator.py
# Simple rule-based coefficients (approximate)
COEFS = {
    "car_kg_per_km": 0.12,    # kg CO2 per km
    "bus_kg_per_km": 0.05,
    "bike_kg_per_km": 0.0,
    "walk_kg_per_km": 0.0,
    "kwh_kg_per_kwh": 0.7,    # kg CO2 per kWh (example)
    "veg_meal_kg": 1.7,
    "nonveg_meal_kg": 3.3,
    "water_kg_per_l": 0.0003  # negligible but included
}

def calculate_carbon_for_entry(entry: dict) -> float:
    """
    Entry keys: travel_km, travel_mode, electricity_kwh, food, water_liters
    Return total kg CO2
    """
    travel_km = float(entry.get("travel_km", 0) or 0)
    mode = (entry.get("travel_mode") or "car").lower()
    electricity_kwh = float(entry.get("electricity_kwh", 0) or 0)
    food = (entry.get("food") or "veg").lower()
    water = float(entry.get("water_liters", 0) or 0)

    travel_coef = COEFS["car_kg_per_km"]
    if mode == "bus":
        travel_coef = COEFS["bus_kg_per_km"]
    elif mode == "bike":
        travel_coef = COEFS["bike_kg_per_km"]
    elif mode == "walk":
        travel_coef = COEFS["walk_kg_per_km"]

    travel_kg = travel_km * travel_coef
    electricity_kg = electricity_kwh * COEFS["kwh_kg_per_kwh"]
    food_kg = COEFS["veg_meal_kg"] if food == "veg" else COEFS["nonveg_meal_kg"]
    water_kg = water * COEFS["water_kg_per_l"]

    total = travel_kg + electricity_kg + food_kg + water_kg
    # round to 2 decimals
    return round(total, 2)
