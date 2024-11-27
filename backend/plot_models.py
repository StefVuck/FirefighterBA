# plot_models.py
from app import create_app
from app.models import PressureCalculationModel, Firefighter, HistoricalBAEntry
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

"""
Simple GPTed script to plot the information for us, doesnt work amazing, but its good enough :)
"""

def plot_models():
    app = create_app()
    with app.app_context():
        firefighters = Firefighter.query.all()
        models = PressureCalculationModel.query.all()
        
        # Create subplot grid
        fig, axes = plt.subplots(3, 2, figsize=(15, 20))
        axes = axes.flatten()
        
        # Plot default model first
        default_model = next(m for m in models if m.is_default)
        pressures = np.linspace(150, 300, 100)
        times = [default_model.calculate_time(p) for p in pressures]
        axes[0].plot(pressures, times, 'b-', label='Default Model')
        axes[0].plot([150, 300], [17, 38], 'r--', label='Target (38min@300, 17min@150)')
        axes[0].set_title('Default Model')
        axes[0].set_xlabel('Pressure (bar)')
        axes[0].set_ylabel('Time (minutes)')
        axes[0].legend()
        axes[0].grid(True)
        
        # Plot each firefighter's data and model
        for i, firefighter in enumerate(firefighters, 1):
            ax = axes[i]
            
            # Get historical data
            history = HistoricalBAEntry.query.filter_by(
                firefighter_id=firefighter.id
            ).order_by(HistoricalBAEntry.session_date.desc()).all()
            
            # Plot historical points
            initial_points = [(h.initial_pressure, h.duration) for h in history]
            final_points = [(h.final_pressure, 0) for h in history]
            
            x_initial = [p[0] for p in initial_points]
            y_initial = [p[1] for p in initial_points]
            x_final = [p[0] for p in final_points]
            y_final = [p[1] for p in final_points]
            
            ax.scatter(x_initial, y_initial, color='blue', alpha=0.5, label='Initial Points')
            ax.scatter(x_final, y_final, color='red', alpha=0.5, label='Final Points')
            
            # Get and plot custom model
            custom_model = next(m for m in models if m.name.endswith(f"{firefighter.first_name} {firefighter.last_name}"))
            times = [custom_model.calculate_time(p) for p in pressures]
            ax.plot(pressures, times, 'g-', label='Fitted Model')
            
            # Plot target line
            if i == 1:  # High consumer
                ax.plot([150, 300], [19, 42], 'r--', label='Target')
            elif i == 2:  # Average
                ax.plot([150, 300], [17, 38], 'r--', label='Target')
            elif i == 3:  # Low
                ax.plot([150, 300], [15, 34], 'r--', label='Target')
            elif i == 4:  # Inconsistent
                ax.plot([150, 300], [18, 40], 'r--', label='Target')
            else:  # Very consistent
                ax.plot([150, 300], [16, 36], 'r--', label='Target')
            
            ax.set_title(f'Firefighter {firefighter.first_name} {firefighter.last_name}')
            ax.set_xlabel('Pressure (bar)')
            ax.set_ylabel('Time (minutes)')
            ax.legend()
            ax.grid(True)
            
            # Add model stats
            stats_text = f'Model predictions:\n'
            stats_text += f'300 bar: {custom_model.calculate_time(300)}min\n'
            stats_text += f'150 bar: {custom_model.calculate_time(150)}min\n'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('model_analysis.png')
        print("Plot saved as model_analysis.png")

if __name__ == "__main__":
    plot_models()