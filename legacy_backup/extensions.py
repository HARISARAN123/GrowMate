# another_module.py
from extensions import db
from app import User  # Example usage of a model

# Query users
users = User.query.all()
