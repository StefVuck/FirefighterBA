from app import create_app, db
from app.models import Firefighter, HistoricalBAEntry, PressureCalculationModel, BAEntry
from datetime import datetime, timedelta
import random

"""
This database initializer script sets up a test database for the BA Board Management System.
It performs the following:

1. Creates a new Flask application context and initializes database tables
2. Clears any existing data and recreates empty tables
3. Generates test data including:
   - 5 test firefighters with sequential badge numbers (FF001-FF005)
   - A pressure calculation model for estimating remaining air time
   - Historical BA entry data for training the model
   - Sample active and inactive BA entries

The script uses helper functions to:
- Create the app context and database connection
- Generate realistic test data with randomized but plausible values
- Calculate standard air consumption times based on pressure readings
- Insert all test records while maintaining referential integrity

This provides a consistent starting state for development and testing.
"""

def create_app_context():
    app = create_app()
    app.app_context().push()
    return app

def clear_database():
    db.drop_all()
    db.create_all()

def create_firefighters():
    firefighters = [
        Firefighter(
            badge_number=f"FF{i:03d}",
            first_name=f"Test{i}",
            last_name=f"Firefighter{i}",
            active=True
        ) for i in range(1, 6)
    ]
    db.session.add_all(firefighters)
    db.session.commit()
    return firefighters

def get_standard_time(pressure: int) -> float:
    """
    Get the standard time for a given pressure using linear interpolation
    between known points
    """
    PRESSURE_DURATION_MAP = {
        300: 38, 290: 37, 280: 35, 270: 34, 260: 32,
        250: 31, 240: 30, 230: 29, 220: 28, 210: 27,
        200: 25, 190: 23, 180: 22, 170: 20, 160: 19,
        150: 17
    }
    
    if pressure in PRESSURE_DURATION_MAP:
        return PRESSURE_DURATION_MAP[pressure]
    
    # Find nearest pressure points for interpolation
    pressures = sorted(PRESSURE_DURATION_MAP.keys())
    for i in range(len(pressures) - 1):
        if pressures[i] <= pressure <= pressures[i + 1]:
            p1, p2 = pressures[i], pressures[i + 1]
            t1, t2 = PRESSURE_DURATION_MAP[p1], PRESSURE_DURATION_MAP[p2]
            # Linear interpolation
            return t1 + (t2 - t1) * (pressure - p1) / (p2 - p1)
    
    return PRESSURE_DURATION_MAP[min(pressure, 300)]

def create_historical_entries(firefighters, calculation_model):
    now = datetime.utcnow()
    entries = []
    
    # Standard pressure to duration mapping
    PRESSURE_DURATION_MAP = {
        300: 38, 290: 37, 280: 35, 270: 34, 260: 32,
        250: 31, 240: 30, 230: 29, 220: 28, 210: 27,
        200: 25, 190: 23, 180: 22, 170: 20, 160: 19,
        150: 17
    }
    
    consumption_patterns = {
        # index: (multiplier, variation)
        0: (1.11, 0.05),  # High consumer (+11%, 5% variation)
        1: (1.0, 0.05),   # Average consumer (standard times, 5% variation)
        2: (0.89, 0.05),  # Low consumer (-11%, 5% variation)
        3: (1.05, 0.15),  # Inconsistent consumer (+5%, 15% variation)
        4: (0.95, 0.03),  # Very consistent consumer (-5%, 3% variation)
    }
    
    for ff_idx, firefighter in enumerate(firefighters):
        pattern = consumption_patterns[ff_idx]
        multiplier = pattern[0]
        variation = pattern[1]
        
        for i in range(10):
            entry_date = now - timedelta(days=i*3)
            
            # Select random starting pressure
            initial_pressure = random.choice(list(PRESSURE_DURATION_MAP.keys()))
            final_pressure = max(150, initial_pressure - random.randint(100, 140))
            
            # Get expected duration from standard times
            expected_duration = PRESSURE_DURATION_MAP[initial_pressure] * multiplier
            
            # Add variation as a percentage
            variation_amount = expected_duration * variation
            actual_duration = int(expected_duration + random.uniform(-variation_amount, variation_amount))
            actual_duration = max(actual_duration, 15)  # Minimum 15 minutes
            
            entry = HistoricalBAEntry(
                firefighter_id=firefighter.id,
                calculation_model_id=calculation_model.id,
                session_date=entry_date,
                initial_pressure=initial_pressure,
                final_pressure=final_pressure,
                duration=actual_duration,
                location=f"Training Area {random.randint(1,5)}"
            )
            entries.append(entry)
    
    db.session.add_all(entries)
    db.session.commit()

def create_default_model():
    """Creates the default model based on the standard chart"""
    # Use two points to calculate slope and intercept
    time_300 = 38
    time_150 = 17
    
    slope = (time_300 - time_150) / 150
    intercept = time_150 - (slope * 150)
    
    default_model = PressureCalculationModel(
        name="Standard Linear Model",
        description="Standard consumption model based on pressure-duration chart",
        slope=slope,
        intercept=intercept,
        max_pressure=300,
        min_pressure=150,
        is_default=True
    )
    
    db.session.add(default_model)
    db.session.commit()
    return default_model

def create_active_entries(firefighters, calculation_model):
    entries = []
    
    for firefighter in firefighters[:2]:
        entry = BAEntry(
            firefighter_id=firefighter.id,
            calculation_model_id=calculation_model.id,
            initial_pressure=290,
            current_pressure=260,
            entry_time=datetime.utcnow() - timedelta(minutes=15),
            location="Active Incident",
            estimated_time=35,
            active=True
        )
        entries.append(entry)
    
    db.session.add_all(entries)
    db.session.commit()

def populate_database():
    print("Creating app context...")
    app = create_app_context()
    
    print("Clearing existing database...")
    clear_database()
    
    print("Creating firefighters...")
    firefighters = create_firefighters()
    
    print("Creating default calculation model...")
    default_model = create_default_model()
    
    print("Creating historical entries...")
    create_historical_entries(firefighters, default_model)
    
    print("Creating active entries...")
    create_active_entries(firefighters, default_model)
    
    print("\nDatabase populated with test data:")
    print(f"- {len(firefighters)} firefighters with consumption patterns:")
    print("1. High consumer (+11% duration, normal variation)")
    print("2. Average consumer (standard durations, normal variation)")
    print("3. Low consumer (-11% duration, normal variation)")
    print("4. Inconsistent consumer (+5% duration, high variation)")
    print("5. Very consistent consumer (-5% duration, low variation)")

if __name__ == "__main__":
    populate_database()