from app import db
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class Firefighter(db.Model):
    """Represents a firefighter in the system"""
    id: int
    badge_number: str
    first_name: str
    last_name: str
    active: bool
    created_at: datetime
    custom_model_id: Optional[int]  # New field to link to custom calculation model

    __tablename__ = 'firefighters'

    id = db.Column(db.Integer, primary_key=True)
    badge_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    custom_model_id = db.Column(db.Integer, db.ForeignKey('pressure_calculation_models.id'), nullable=True)

    # Add relationship to custom model
    custom_model = db.relationship('PressureCalculationModel', foreign_keys=[custom_model_id])

@dataclass
class PressureCalculationModel(db.Model):
    """Defines how to calculate remaining time based on pressure"""
    id: int
    name: str
    description: str
    slope: float
    intercept: float
    max_pressure: int
    min_pressure: int
    is_default: bool
    firefighter_id: Optional[int]  # New field to identify custom models

    __tablename__ = 'pressure_calculation_models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    slope = db.Column(db.Float, nullable=False)  # Rate of time change per bar
    intercept = db.Column(db.Float, nullable=False)  # Base time
    max_pressure = db.Column(db.Integer, nullable=False, default=300)
    min_pressure = db.Column(db.Integer, nullable=False, default=150)
    is_default = db.Column(db.Boolean, default=False)
    firefighter_id = db.Column(db.Integer, db.ForeignKey('firefighters.id'), nullable=True)

    @classmethod
    def get_default_model(cls):
        """Creates the default linear model (38min@300bar to 17min@150bar)"""
        slope = (38 - 17) / (300 - 150)  # Time change per bar
        intercept = 17 - (slope * 150)    # Base time at 0 bar
        return cls(
            name="Standard Linear Model",
            description="Linear model from 38min@300bar to 17min@150bar",
            slope=slope,
            intercept=intercept,
            max_pressure=300,
            min_pressure=150,
            is_default=True
        )

    @classmethod
    def get_model_for_firefighter(cls, firefighter_id: int):
        """Get the appropriate calculation model for a firefighter"""
        # First try to get firefighter's custom model
        firefighter = Firefighter.query.get(firefighter_id)
        if firefighter and firefighter.custom_model_id:
            return cls.query.get(firefighter.custom_model_id)
        
        # Fall back to default model if no custom model exists
        return cls.query.filter_by(is_default=True).first() or cls.get_default_model()

    def calculate_time(self, pressure: int) -> int:
        """Calculate remaining time for given pressure"""
        if pressure > self.max_pressure:
            pressure = self.max_pressure
        elif pressure < self.min_pressure:
            pressure = self.min_pressure
        
        return round((self.slope * pressure) + self.intercept)

@dataclass
class BAEntry(db.Model):
    """Records a firefighter's BA session"""
    id: int
    firefighter_id: int
    calculation_model_id: int
    initial_pressure: int
    current_pressure: int
    entry_time: datetime
    location: str
    remarks: Optional[str]
    estimated_time: int
    updated_time: datetime
    active: bool

    __tablename__ = 'ba_entries'

    id = db.Column(db.Integer, primary_key=True)
    firefighter_id = db.Column(db.Integer, db.ForeignKey('firefighters.id'), nullable=False)
    calculation_model_id = db.Column(db.Integer, db.ForeignKey('pressure_calculation_models.id'), nullable=False)
    initial_pressure = db.Column(db.Integer, nullable=False)
    current_pressure = db.Column(db.Integer, nullable=False)
    entry_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location = db.Column(db.String(200))
    remarks = db.Column(db.String(500))
    estimated_time = db.Column(db.Integer, nullable=False)
    updated_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    # Add relationships
    firefighter = db.relationship('Firefighter', backref='ba_entries')
    calculation_model = db.relationship('PressureCalculationModel')

@dataclass
class HistoricalBAEntry(db.Model):
    """Historical record of completed BA sessions"""
    id: int
    firefighter_id: int
    session_date: datetime
    initial_pressure: int
    final_pressure: int
    duration: int
    location: str
    calculation_model_id: int

    __tablename__ = 'historical_ba_entries'

    id = db.Column(db.Integer, primary_key=True)
    firefighter_id = db.Column(db.Integer, db.ForeignKey('firefighters.id'), nullable=False)
    calculation_model_id = db.Column(db.Integer, db.ForeignKey('pressure_calculation_models.id'), nullable=False)
    session_date = db.Column(db.DateTime, nullable=False)
    initial_pressure = db.Column(db.Integer, nullable=False)
    final_pressure = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200))

    # Add relationships
    firefighter = db.relationship('Firefighter', backref='historical_entries')
    calculation_model = db.relationship('PressureCalculationModel')