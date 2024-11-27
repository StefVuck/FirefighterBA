## Insallations
pip install -r backend/requirements.txt

## Starting Backend
cd backend
python init_db.py  # Only first time
flask run


## Starting Frontend
cd frontend
npm install
npm run dev

## Basic View
![image](https://github.com/user-attachments/assets/d3fe5995-3754-406d-8a41-f55f4199e71d)


## Mermaid UML
```mermaid
erDiagram
    Firefighter ||--o{ BAEntry : "has"
    Firefighter ||--o{ HistoricalBAEntry : "has"
    Firefighter ||--o{ PressureCalculationModel : "has custom"
    PressureCalculationModel ||--o{ BAEntry : "used by"
    PressureCalculationModel ||--o{ HistoricalBAEntry : "used by"

    Firefighter {
        int id PK
        string badge_number UK
        string first_name
        string last_name
        boolean active
        datetime created_at
        int custom_model_id FK
    }

    PressureCalculationModel {
        int id PK
        string name
        string description
        float slope
        float intercept
        int max_pressure
        int min_pressure
        boolean is_default
        int firefighter_id FK
    }

    BAEntry {
        int id PK
        int firefighter_id FK
        int calculation_model_id FK
        int initial_pressure
        int current_pressure
        datetime entry_time
        string location
        string remarks
        int estimated_time
        datetime updated_time
        boolean active
    }

    HistoricalBAEntry {
        int id PK
        int firefighter_id FK
        int calculation_model_id FK
        datetime session_date
        int initial_pressure
        int final_pressure
        int duration
        string location
    }
```
