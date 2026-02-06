from database import Base, engine
from models import (
    User, Node, NodeMember, Content, Chapter,
    SocialLink, NodeSocialLink, Invitation
)

def init_db():
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")

if __name__ == "__main__":
    init_db()
