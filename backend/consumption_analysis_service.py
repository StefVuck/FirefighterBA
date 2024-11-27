from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np
from datetime import datetime
import time

from app import create_app
from app.models import (
    Firefighter, 
    HistoricalBAEntry, 
    PressureCalculationModel,
    BAEntry,
    db
)

class ConsumptionAnalysisService:
    """
    Service for analyzing firefighter breathing apparatus consumption patterns and creating personalized models.
    Processes historical BA data to generate customized pressure-duration calculation models for each firefighter.
    """
    def __init__(self, min_entries: int = 5):
        # Initialize the consumption analysis service.
        self.app = create_app()
        self.min_entries = min_entries
        # Standard pressure-duration map based on typical consumption rates
        # Maps cylinder pressure (in bar) to expected duration (in minutes)
        self.PRESSURE_DURATION_MAP = {
            300: 38, 290: 37, 280: 35, 270: 34, 260: 32,
            250: 31, 240: 30, 230: 29, 220: 28, 210: 27,
            200: 25, 190: 23, 180: 22, 170: 20, 160: 19,
            150: 17
        }

    def get_standard_time(self, pressure: int) -> float:
        # Get standard duration time for a given pressure using linear interpolation between known points.
        if pressure in self.PRESSURE_DURATION_MAP:
            return self.PRESSURE_DURATION_MAP[pressure]
        
        pressures = sorted(self.PRESSURE_DURATION_MAP.keys())
        for i in range(len(pressures) - 1):
            if pressures[i] <= pressure <= pressures[i + 1]:
                p1, p2 = pressures[i], pressures[i + 1]
                t1, t2 = self.PRESSURE_DURATION_MAP[p1], self.PRESSURE_DURATION_MAP[p2]
                return t1 + (t2 - t1) * (pressure - p1) / (p2 - p1)
        
        return self.PRESSURE_DURATION_MAP[min(max(pressure, 150), 300)]

    def create_consumption_model(self, firefighter_id: int):
        """
        Create a personalized consumption model for a firefighter based on their historical data.
        
        Returns:
            A PressureCalculationModel instance - either personalized or default if insufficient data
        """
        data_points = self.get_firefighter_data(firefighter_id)
        if len(data_points) < self.min_entries:
            return PressureCalculationModel.get_default_model()

        # Calculate how firefighter's actual times differ from standard times
        ratios = []
        for pressure, actual_time in data_points:
            if actual_time > 0:  # Ignore zero-time points
                standard_time = self.get_standard_time(pressure)
                ratio = actual_time / standard_time
                ratios.append(ratio)

        if not ratios:
            return PressureCalculationModel.get_default_model()

        # Use median ratio to create personalized model resistant to outliers
        consumption_ratio = np.median(ratios)
        
        # Calculate slope and intercept for linear model using adjusted standard times
        time_300 = self.PRESSURE_DURATION_MAP[300] * consumption_ratio
        time_150 = self.PRESSURE_DURATION_MAP[150] * consumption_ratio
        
        slope = (time_300 - time_150) / 150
        intercept = time_150 - (slope * 150)

        with self.app.app_context():
            firefighter = Firefighter.query.get(firefighter_id)
            return PressureCalculationModel(
                name=f"Custom Model - {firefighter.first_name} {firefighter.last_name}",
                description=f"Personalized model based on {len(data_points)} points (consumption ratio={consumption_ratio:.2f})",
                slope=slope,
                intercept=intercept,
                max_pressure=300,
                min_pressure=150,
                is_default=False,
                firefighter_id=firefighter_id
            )

    def get_firefighter_data(self, firefighter_id: int):
        """
        Retrieve historical BA entry data for a firefighter.
            
        Returns:
            List of tuples containing (initial_pressure, duration) from historical entries
        """
        with self.app.app_context():
            entries = HistoricalBAEntry.query.filter_by(
                firefighter_id=firefighter_id
            ).order_by(HistoricalBAEntry.session_date.desc()).all()

            data_points = []
            for entry in entries:
                # Only use initial pressure points for better accuracy
                data_points.append((entry.initial_pressure, entry.duration))

            return data_points

    def update_firefighter_models(self):
        """
        Update consumption models for all active firefighters.
        Creates new models or updates existing ones based on latest historical data.
        Also updates any active BA entries with new time estimates.
        """
        with self.app.app_context():
            firefighters = Firefighter.query.filter_by(active=True).all()
            
            for firefighter in firefighters:
                try:
                    # Get existing custom model
                    existing_model = PressureCalculationModel.query.filter_by(
                        firefighter_id=firefighter.id,
                        is_default=False
                    ).first()

                    # Create new model
                    new_model = self.create_consumption_model(firefighter.id)
                    
                    if existing_model:
                        # Update existing model
                        existing_model.slope = new_model.slope
                        existing_model.intercept = new_model.intercept
                        existing_model.description = new_model.description
                    else:
                        # Add new model
                        db.session.add(new_model)
                        firefighter.custom_model_id = new_model.id
                    
                    # Update active BA entries
                    active_entries = BAEntry.query.filter_by(
                        firefighter_id=firefighter.id,
                        active=True
                    ).all()
                    
                    model_to_use = existing_model if existing_model else new_model
                    
                    for entry in active_entries:
                        entry.calculation_model_id = model_to_use.id
                        entry.estimated_time = model_to_use.calculate_time(entry.current_pressure)
                    
                    db.session.commit()
                    print(f"Updated model for {firefighter.first_name} {firefighter.last_name}")
                    
                except Exception as e:
                    print(f"Error updating model for firefighter {firefighter.id}: {str(e)}")
                    db.session.rollback()

    def run(self):
        while True:
            print(f"Starting consumption analysis at {datetime.now()}")
            self.update_firefighter_models()


if __name__ == "__main__":
    service = ConsumptionAnalysisService()
    service.run()