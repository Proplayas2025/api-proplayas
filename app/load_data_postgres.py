"""
Script para cargar datos desde CSVs a PostgreSQL.
Lee nodes.csv y users.csv, hashea contraseñas con bcrypt, y limpia/recarga la BD.

Uso:
  Local: python scripts/load_data_postgres.py
  Docker: docker exec proplayas-api-dev python scripts/load_data_postgres.py
"""
import csv
import bcrypt
import sys
import os
from pathlib import Path

# Agregar el directorio api-proplayas al path
sys.path.insert(0, str(Path(__file__).parent.parent / "api-proplayas" / "app"))

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base
from models.node import Node, NodeType, NodeStatus
from models.user import User, UserRole, UserStatus
from models.node_member import NodeMember

# Rutas de los CSVs
# EN DOCKER: El proyecto está montado en /app, CSVs en /app/nodes.csv
# Los CSVs pueden estar en el directorio actual o un nivel arriba
script_dir = Path(__file__).parent.absolute()

# Buscar los CSVs en múltiples ubicaciones posibles
possible_nodes = [
    script_dir / "nodes.csv",
    script_dir.parent / "nodes.csv",
    Path("/app/nodes.csv"),
]
possible_users = [
    script_dir / "users.csv",
    script_dir.parent / "users.csv",
    Path("/app/users.csv"),
]

NODES_CSV = next((p for p in possible_nodes if p.exists()), None)
USERS_CSV = next((p for p in possible_users if p.exists()), None)

# Determinar la URL de base de datos
# Si estamos en Docker (contenedor), usar 'postgres', si no, usar 'localhost'
# Detectar Docker: verifica si existe /.dockerenv
IN_DOCKER = Path("/.dockerenv").exists()
DEFAULT_DB_HOST = "postgres" if IN_DOCKER else "localhost"

DB_HOST = os.getenv("DB_HOST", DEFAULT_DB_HOST)
DB_USER = os.getenv("DB_USER", "proplayas")
DB_PASSWORD = os.getenv("DB_PASSWORD", "proplayas")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "proplayas_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def load_nodes(session):
    """Carga nodos desde nodes.csv."""
    print("Cargando nodos desde nodes.csv...")
    
    nodes_dict = {}  # Para mapear code -> Node object
    
    with open(NODES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node = Node(
                code=row["code"],
                name=row["name"],
                type=NodeType(row["type"]),
                country=row["country"].strip() if row["country"] else None,
                city=row["city"].strip() if row["city"] else None,
                joined_in=int(row["joined_in"]) if row["joined_in"] else None,
                status=NodeStatus.active,
                members_count=0
            )
            session.add(node)
            nodes_dict[row["code"]] = node
    
    session.commit()
    print(f"✓ {len(nodes_dict)} nodos cargados")
    return nodes_dict

def load_users(session, nodes_dict):
    """Carga usuarios desde users.csv y los relaciona con nodos."""
    print("Cargando usuarios desde users.csv...")
    
    user_count = 0
    leader_pairs = []  # (node, user) para asignar leader_id después del flush
    
    with open(USERS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Obtener el nodo correspondiente al code del usuario
            node_code = row["code"].strip()
            node = nodes_dict.get(node_code)
            
            if not node:
                print(f"⚠ Nodo {node_code} no encontrado para usuario {row['name']}, saltando...")
                continue
            
            # Hashear la contraseña
            hashed_password = hash_password(row["password"].strip())
            
            # Limpiar email (algunos tienen espacios al final en el CSV)
            email = row["email"].strip()
            username = row["username"].strip() if row["username"] and row["username"].strip() else email.split("@")[0]
            
            # Crear usuario
            user = User(
                name=row["name"].strip(),
                email=email,
                username=username,
                password=hashed_password,
                role=UserRole(row["role"].strip()),
                status=UserStatus.active,
                degree=row["degree"].strip() if row.get("degree") and row["degree"].strip() else None,
                postgraduate=row["postgraduate"].strip() if row.get("postgraduate") and row["postgraduate"].strip() else None,
                expertise_area=row["expertise_area"].strip() if row.get("expertise_area") and row["expertise_area"].strip() else None,
                research_line=row["research_line"].strip() if row.get("research_line") and row["research_line"].strip() else None,
                country=row["country"].strip() if row.get("country") and row["country"].strip() else None,
                city=row["city"].strip() if row.get("city") and row["city"].strip() else None,
                node_id=node.id  # Relacionar usuario con su nodo
            )
            
            session.add(user)
            
            # Guardar par para asignar leader_id después
            if row["role"].strip() == "node_leader":
                leader_pairs.append((node, user))
            
            user_count += 1
    
    # Flush para que los usuarios obtengan sus IDs de la BD
    session.flush()
    
    # Ahora que los usuarios tienen ID, asignar leader_id a cada nodo
    for node, user in leader_pairs:
        node.leader_id = user.id
        node.members_count = 1
        
        # Crear registro NodeMember para que el líder aparezca en la lista de miembros
        leader_member = NodeMember(
            user_id=user.id,
            node_id=node.id,
            member_code=node.code,  # Líder usa el código del nodo (ej: A01)
        )
        session.add(leader_member)
    
    session.commit()
    print(f"✓ {user_count} usuarios cargados")
    print(f"✓ {len(leader_pairs)} nodos con líder asignado (con NodeMember)")

def clear_database(engine):
    """Limpia todas las tablas de la BD."""
    print("Limpiando la base de datos...")
    
    with engine.connect() as conn:
        # Desactivar constraints temporalmente
        conn.execute(text("SET session_replication_role = 'replica'"))
        
        # Eliminar todas las filas de todas las tablas
        conn.execute(text("DO $$ DECLARE r RECORD; BEGIN FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE'; END LOOP; END $$;"))
        
        # Reactivar constraints
        conn.execute(text("SET session_replication_role = 'origin'"))
        conn.commit()
    
    print("✓ Base de datos limpiada")

def main():
    """Función principal."""
    print("="*60)
    print("SCRIPT DE CARGA DE DATOS A POSTGRESQL")
    print("="*60)
    print(f"BD Host: {DB_HOST}:{DB_PORT}")
    print(f"BD Name: {DB_NAME}")
    print(f"Nodes CSV: {NODES_CSV}")
    print(f"Users CSV: {USERS_CSV}")
    print()
    
    # Verificar archivos
    if NODES_CSV is None or not NODES_CSV.exists():
        print(f"❌ Error: nodes.csv no encontrado")
        print(f"   Buscado en: {possible_nodes}")
        return
    
    if USERS_CSV is None or not USERS_CSV.exists():
        print(f"❌ Error: users.csv no encontrado")
        print(f"   Buscado en: {possible_users}")
        return
    
    # Crear engine y session
    print("Conectando a la base de datos...")
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,  # Verificar conexión antes de usar
            connect_args={"connect_timeout": 10}
        )
        
        # Probar la conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Conexión exitosa")
        print()
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print()
        if IN_DOCKER:
            print("Estás DENTRO de Docker. Soluciones:")
            print("1. Verifica que PostgreSQL esté corriendo:")
            print("   docker compose ps")
            print("2. Si PostgreSQL no está corriendo, levántalo:")
            print("   docker compose up -d postgres")
            print("3. Verifica que 'proplayas-postgres-dev' esté en estado 'healthy'")
        else:
            print("Estás FUERA de Docker. Soluciones:")
            print("1. Asegúrate de que PostgreSQL esté corriendo:")
            print("   docker compose up -d postgres")
            print("2. Usa la variable DB_HOST para especificar el host:")
            print("   DB_HOST=localhost python load_data_postgres.py")
        print()
        print(f"Configuración actual:")
        print(f"  DB_HOST: {DB_HOST}")
        print(f"  DATABASE_URL: {DATABASE_URL}")
        return
    
    # Crear todas las tablas
    print("Creando tablas...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Tablas creadas/verificadas")
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        return
    
    print()
    
    # Limpiar BD
    try:
        clear_database(engine)
    except Exception as e:
        print(f"❌ Error al limpiar BD: {e}")
        return
    
    print()
    
    # Crear session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Cargar datos
        nodes_dict = load_nodes(session)
        load_users(session, nodes_dict)
        
        print()
        print("="*60)
        print("✓ DATOS CARGADOS EXITOSAMENTE")
        print("="*60)
        print()
        print("Usuarios de prueba:")
        print("  Admin: admin@proplayas.org / ProplayasA01!")
        print("  Node Leader: solmattos1968@gmail.com / ProplayasA01!")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    main()
