from flask import Blueprint, request, jsonify
from app.models import Firefighter, PressureCalculationModel, BAEntry, HistoricalBAEntry
from app import db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any

main_bp = Blueprint('main', __name__)
"""
This module defines the API routes for the BA Board Management System.
It handles HTTP requests for managing firefighters, BA entries, and pressure calculations.
Includes endpoints for:
- Creating and retrieving firefighters
- Managing BA entries and historical data
- Calculating remaining air time using personalized models
"""

# Helper function to serialize response
def create_response(data: Dict[str, Any], status: int = 200) -> tuple:
    return jsonify(data), status


@main_bp.route('/api/firefighters', methods=['POST'])
def add_firefighter():
    try:
        data = request.json
        new_firefighter = Firefighter(
            badge_number=data['badge_number'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        
        db.session.add(new_firefighter)
        db.session.commit()
        
        return create_response(new_firefighter, 201)
    except SQLAlchemyError as e:
        db.session.rollback()
        return create_response({'error': str(e)}, 500)


@main_bp.route('/api/firefighters', methods=['GET'])
def get_firefighters():
    try:
        firefighters = Firefighter.query.filter_by(active=True).all()
        return create_response(firefighters)
    except SQLAlchemyError as e:
        return create_response({'error': str(e)}, 500)


@main_bp.route('/api/ba-entries', methods=['POST'])
def create_ba_entry():
    try:
        data = request.json
        firefighter = Firefighter.query.get_or_404(data['firefighter_id'])
        
        # Get appropriate calculation model for this firefighter
        calc_model = PressureCalculationModel.get_model_for_firefighter(firefighter.id)
        
        # Calculate initial estimated time
        estimated_time = calc_model.calculate_time(data['initial_pressure'])
        
        new_entry = BAEntry(
            firefighter_id=firefighter.id,
            calculation_model_id=calc_model.id,
            initial_pressure=data['initial_pressure'],
            current_pressure=data['initial_pressure'],
            location=data['location'],
            remarks=data.get('remarks', ''),
            estimated_time=estimated_time
        )
        
        db.session.add(new_entry)
        db.session.commit()
        
        return create_response(new_entry, 201)
    except SQLAlchemyError as e:
        db.session.rollback()
        return create_response({'error': str(e)}, 500)


@main_bp.route('/api/ba-entries', methods=['GET'])
def get_ba_entries():
    try:
        active_only = request.args.get('active', 'true').lower() == 'true'
        if active_only:
            entries = BAEntry.query.filter_by(active=True).all()
        else:
            entries = BAEntry.query.all()
        return create_response(entries)
    except SQLAlchemyError as e:
        return create_response({'error': str(e)}, 500)


@main_bp.route('/api/ba-entries/<int:entry_id>', methods=['PUT'])
def update_ba_entry(entry_id):
    try:
        entry = BAEntry.query.get_or_404(entry_id)
        data = request.json
        
        if 'current_pressure' in data:
            entry.current_pressure = data['current_pressure']
            entry.estimated_time = entry.calculation_model.calculate_time(data['current_pressure'])
            entry.updated_time = datetime.utcnow()
            
            # Check if pressure is at or below minimum
            if data['current_pressure'] <= entry.calculation_model.min_pressure:
                entry.active = False
                
                # Create historical record
                duration = round((datetime.utcnow() - entry.entry_time).total_seconds() / 60)
                historical_record = HistoricalBAEntry(
                    firefighter_id=entry.firefighter_id,
                    calculation_model_id=entry.calculation_model_id,
                    session_date=entry.entry_time,
                    initial_pressure=entry.initial_pressure,
                    final_pressure=data['current_pressure'],
                    duration=duration,
                    location=entry.location
                )
                db.session.add(historical_record)
        
        if 'location' in data:
            entry.location = data['location']
        if 'remarks' in data:
            entry.remarks = data['remarks']
            
        db.session.commit()
        return create_response(entry)
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return create_response({'error': str(e)}, 500)


@main_bp.route('/api/historical', methods=['GET'])
def get_historical_entries():
    try:
        entries = HistoricalBAEntry.query.all()
        return create_response(entries)
    except SQLAlchemyError as e:
        return create_response({'error': str(e)}, 500)
    

# Add new endpoint to manually trigger analysis for a firefighter
@main_bp.route('/api/firefighters/<int:firefighter_id>/analyze', methods=['POST'])
def analyze_firefighter(firefighter_id):
    try:
        from ..consumption_analysis_service import ConsumptionAnalysisService
        from flask import current_app
        
        service = ConsumptionAnalysisService(current_app.config['SQLALCHEMY_DATABASE_URI'])
        firefighter = Firefighter.query.get_or_404(firefighter_id)
        
        new_model = service.create_consumption_model(firefighter_id)
        if new_model:
            db.session.add(new_model)
            firefighter.custom_model_id = new_model.id
            db.session.commit()
            
        return create_response({'message': 'Analysis complete', 'model_id': new_model.id})
    except Exception as e:
        db.session.rollback()
        return create_response({'error': str(e)}, 500)
    

@main_bp.route('/api/firefighters/<int:firefighter_id>/predictions/<int:pressure>')
def get_time_predictions(firefighter_id, pressure):
    try:
        # Get default model
        default_model = PressureCalculationModel.query.filter_by(is_default=True).first()
        if not default_model:
            default_model = PressureCalculationModel.get_default_model()
        
        # Get custom model for firefighter
        custom_model = PressureCalculationModel.query.filter_by(
            firefighter_id=firefighter_id,
            is_default=False
        ).first()
        
        # Calculate predictions
        default_time = default_model.calculate_time(pressure)
        custom_time = custom_model.calculate_time(pressure) if custom_model else default_time
        
        return jsonify({
            'default': default_time,
            'custom': custom_time
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500