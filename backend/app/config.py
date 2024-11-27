import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ba_board.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
