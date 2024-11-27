# verify_models.py
from app import create_app
from app.models import PressureCalculationModel, Firefighter
from datetime import datetime

def verify_models():
    app = create_app()
    with app.app_context():
        # Get all models
        models = PressureCalculationModel.query.all()
        
        print("\n=== Model Verification Report ===")
        print(f"Total models: {len(models)}")
        print("\nDetailed Analysis:")
        
        for model in models:
            print(f"\nModel: {model.name}")
            print(f"Description: {model.description}")
            print("Time predictions:")
            print(f"  At 300 bar: {model.calculate_time(300)} minutes")
            print(f"  At 200 bar: {model.calculate_time(200)} minutes")
            print(f"  At 150 bar: {model.calculate_time(150)} minutes")
            
            # Calculate average consumption rate
            consumption_rate = (300 - 150) / (model.calculate_time(300) - model.calculate_time(150))
            print(f"Average consumption rate: {consumption_rate:.2f} bar/min")
            
            if model.firefighter_id:
                firefighter = Firefighter.query.filter_by(id=model.firefighter_id).first()
                print(f"Associated Firefighter: {firefighter.first_name} {firefighter.last_name}")

if __name__ == "__main__":
    verify_models()