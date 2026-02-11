from database import SessionLocal
from models import User
from models.user import UserRole, UserStatus
from core.security import get_password_hash
from core.config import settings

def seed_db():
    db = SessionLocal()
    
    try:
        print("🌱 Sembrando datos de prueba...")
        
        print("  - Creando usuario admin...")
        admin = User(
            name="Admin Proplayas",
            username="admin",
            email="admin@proplayas.org",
            password=get_password_hash("admin123"),
            role=UserRole.admin,
            status=UserStatus.active,
            about="Administrador principal del sistema",
            country="Ecuador",
            city="Quito"
        )
        db.add(admin)
        db.commit()

        print("\n Datos de prueba insertados correctamente:")
        print("   - 1 Admin (admin@proplayas.org / admin123)")
        
    except Exception as e:
        print(f"❌ Error al sembrar datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
