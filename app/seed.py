from datetime import datetime, timedelta
from database import SessionLocal
from models import User, Node, NodeMember, Content, Invitation, SocialLink, NodeSocialLink
from models.user import UserRole, UserStatus
from models.node import NodeType, NodeStatus
from models.content import ContentType, ContentStatus, EventType, EventFormat, PublicationType
from models.invitation import InvitationStatus
from models.social_link import SocialPlatform
from core.security import get_password_hash
from jose import jwt
from core.config import settings

def _make_invitation_token(data: dict) -> str:
    """Crea un JWT para invitaciones de prueba."""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

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
        db.flush()
        
        print("  - Creando nodo de prueba (A01 - sociedad_civil)...")
        node1 = Node(
            name="Nodo Comunidad Costera",
            code="A01",
            type=NodeType.sociedad_civil,
            about="Comunidad dedicada al cuidado de playas en la costa ecuatoriana",
            country="Ecuador",
            city="Manta",
            joined_in=2023,
            members_count=0,
            status=NodeStatus.active,
            leader_id=None
        )
        db.add(node1)
        db.flush()
        
        print("  - Creando líder de nodo...")
        node_leader = User(
            name="María García",
            username="maria.garcia",
            email="maria@proplayas.org",
            password=get_password_hash("leader123"),
            role=UserRole.node_leader,
            status=UserStatus.active,
            about="Bióloga marina especializada en conservación costera",
            degree="Licenciatura en Biología Marina",
            postgraduate="Maestría en Conservación Marina",
            expertise_area="Conservación de ecosistemas costeros",
            research_work="Investigación sobre impacto de microplásticos en playas",
            country="Ecuador",
            city="Manta",
            node_id=node1.id
        )
        db.add(node_leader)
        db.flush()
        
        node1.leader_id = node_leader.id
        
        # Crear NodeMember para el líder (código = código del nodo)
        leader_member = NodeMember(
            user_id=node_leader.id,
            node_id=node1.id,
            member_code="A01",  # El líder tiene el código del nodo
        )
        db.add(leader_member)
        
        print("  - Creando redes sociales del nodo...")
        node_social1 = NodeSocialLink(
            platform=SocialPlatform.facebook,
            url="https://facebook.com/nodocostaecuador",
            node_id=node1.id
        )
        node_social2 = NodeSocialLink(
            platform=SocialPlatform.instagram,
            url="https://instagram.com/nodocostaecuador",
            node_id=node1.id
        )
        db.add_all([node_social1, node_social2])
        
        print("  - Creando miembros del nodo...")
        member1 = User(
            name="Carlos Mendoza",
            username="carlos.mendoza",
            email="carlos@proplayas.org",
            password=get_password_hash("member123"),
            role=UserRole.member,
            status=UserStatus.active,
            about="Estudiante de ciencias ambientales",
            expertise_area="Educación ambiental",
            research_work="Programas de sensibilización comunitaria",
            country="Ecuador",
            city="Manta",
            node_id=node1.id
        )
        
        member2 = User(
            name="Ana Torres",
            username="ana.torres",
            email="ana@proplayas.org",
            password=get_password_hash("member123"),
            role=UserRole.member,
            status=UserStatus.active,
            about="Fotógrafa de naturaleza",
            expertise_area="Documentación visual",
            research_work="Registro fotográfico de biodiversidad costera",
            country="Ecuador",
            city="Manta",
            node_id=node1.id
        )
        db.add_all([member1, member2])
        db.flush()
        
        # Crear NodeMember para cada miembro (A01-1, A01-2)
        nm1 = NodeMember(
            user_id=member1.id,
            node_id=node1.id,
            member_code="A01-1",
            research_line="Educación ambiental",
            work_area="Sensibilización comunitaria",
        )
        nm2 = NodeMember(
            user_id=member2.id,
            node_id=node1.id,
            member_code="A01-2",
            research_line="Documentación visual",
            work_area="Fotografía de biodiversidad",
        )
        db.add_all([nm1, nm2])
        
        node1.members_count = 3  # líder + 2 miembros
        
        print("  - Creando contenido de eventos...")
        event1 = Content(
            title="Limpieza de Playa Murciélago",
            description="Jornada de limpieza comunitaria en Playa Murciélago. Todos son bienvenidos.",
            content_type=ContentType.event,
            status=ContentStatus.published,
            event_type=EventType.event,
            event_format=EventFormat.presencial,
            event_date=datetime.utcnow() + timedelta(days=15),
            location="Playa Murciélago, Manta, Ecuador",
            participants=["Nodo Comunidad Costera", "Municipio de Manta"],
            author_id=node_leader.id,
            node_id=node1.id
        )
        
        event2 = Content(
            title="Taller de Identificación de Microplásticos",
            description="Aprende a identificar y clasificar microplásticos encontrados en playas",
            content_type=ContentType.event,
            status=ContentStatus.published,
            event_type=EventType.taller,
            event_format=EventFormat.online,
            event_date=datetime.utcnow() + timedelta(days=7),
            link="https://zoom.us/j/ejemplo",
            author_id=node_leader.id,
            node_id=node1.id
        )
        db.add_all([event1, event2])
        
        print("  - Creando contenido de publicaciones...")
        pub1 = Content(
            title="Guía de Buenas Prácticas en Playas",
            description="Manual para visitantes sobre cómo cuidar nuestras playas",
            content_type=ContentType.publication,
            status=ContentStatus.published,
            publication_type=PublicationType.guia,
            file_path="guia_buenas_practicas.pdf",
            author_id=member1.id,
            node_id=node1.id
        )
        db.add(pub1)
        
        print("  - Creando contenido de libros...")
        book1 = Content(
            title="Conservación Marina en Ecuador",
            description="Un análisis profundo de los ecosistemas marinos del Ecuador",
            content_type=ContentType.book,
            status=ContentStatus.published,
            book_author="María García, Carlos Mendoza",
            publication_date=datetime(2024, 6, 15),
            isbn="978-9942-123-45-6",
            author_id=node_leader.id,
            node_id=node1.id
        )
        db.add(book1)
        
        print("  - Creando proyectos...")
        project1 = Content(
            title="Proyecto de Restauración Costera",
            description="Iniciativa para restaurar zonas costeras degradadas mediante técnicas de bioingeniería",
            content_type=ContentType.project,
            status=ContentStatus.published,
            location="Costa ecuatoriana",
            participants=["Nodo Comunidad Costera", "Universidad Técnica de Manabí", "Ministerio del Ambiente"],
            link="https://proyecto-restauracion.org",
            author_id=node_leader.id,
            node_id=node1.id
        )
        db.add(project1)
        
        print("  - Creando invitaciones pendientes...")
        # Invitación de miembro (enviada por líder de nodo)
        member_token = _make_invitation_token({
            "name": "Pedro Jiménez",
            "email": "pedro@example.com",
            "role_type": "member",
            "node_code": "A01",
            "node_id": node1.id,
        })
        invitation1 = Invitation(
            name="Pedro Jiménez",
            email="pedro@example.com",
            token=member_token,
            role=UserRole.member,
            status=InvitationStatus.pending,
            node_id=node1.id,
            invited_by=node_leader.id
        )
        
        # Invitación de líder de nodo (enviada por admin)
        leader_token = _make_invitation_token({
            "name": "Laura Sánchez",
            "email": "laura@example.com",
            "role_type": "node_leader",
            "node_type": "cientifico",
            "node_code": "C01",
        })
        invitation2 = Invitation(
            name="Laura Sánchez",
            email="laura@example.com",
            token=leader_token,
            role=UserRole.node_leader,
            node_type="cientifico",
            status=InvitationStatus.pending,
            invited_by=admin.id
        )
        db.add_all([invitation1, invitation2])
        
        db.commit()
        
        print("\n Datos de prueba insertados correctamente:")
        print("   - 1 Admin (admin@proplayas.org / admin123)")
        print("   - 1 Lider de nodo (maria@proplayas.org / leader123)")
        print("   - 2 Miembros (carlos@proplayas.org, ana@proplayas.org / member123)")
        print("   - 1 Nodo (A01 - sociedad_civil)")
        print("   - Codigos de miembro: A01 (lider), A01-1, A01-2")
        print("   - 2 Eventos")
        print("   - 1 Publicacion")
        print("   - 1 Libro")
        print("   - 1 Proyecto")
        print("   - 2 Invitaciones pendientes (JWT tokens)")
        
    except Exception as e:
        print(f"❌ Error al sembrar datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
