from flask_login import UserMixin

from app import db


class User (db.model, UserMixin);
  __tablename__ = 'users'

uid = db.column