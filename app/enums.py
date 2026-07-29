"""Enumeraciones compartidas del dominio.

Fuente única de verdad para los enums usados por modelos ORM y schemas Pydantic.
Los módulos de `models/` las reexportan por compatibilidad con los imports
existentes (ej. `from models.user import UserRole`).
"""
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    node_leader = "node_leader"
    member = "member"


class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


class NodeType(str, Enum):
    sociedad_civil = "sociedad_civil"
    cientifico = "cientifico"
    empresarial = "empresarial"
    funcion_publica = "funcion_publica"
    individual = "individual"


class NodeStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


class SocialPlatform(str, Enum):
    linkedin = "linkedin"
    github = "github"
    twitter = "twitter"
    website = "website"
    facebook = "facebook"
    instagram = "instagram"
    youtube = "youtube"
    research_gate = "research_gate"
    phone = "phone"


class ContentType(str, Enum):
    event = "event"
    publication = "publication"
    book = "book"
    project = "project"
    series = "series"


class ContentStatus(str, Enum):
    inactive = "inactive"
    active = "active"


class EventType(str, Enum):
    event = "event"
    taller = "taller"
    clase = "clase"
    curso = "curso"
    seminario = "seminario"
    foro = "foro"
    conferencia = "conferencia"
    congreso = "congreso"
    webinar = "webinar"


class EventFormat(str, Enum):
    presencial = "presencial"
    online = "online"


class PublicationType(str, Enum):
    boletin = "boletin"
    guia = "guia"
    articulo = "articulo"


class InvitationStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"
