import sys
from app.db.base import Base
from app.models.users import User
from app.models.documents import Document
from app.models.projects import Project, Role, ProjectMember
from sqlalchemy import create_engine

try:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
