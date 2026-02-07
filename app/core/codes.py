from sqlalchemy.orm import Session
from models.node import Node
from models.node_member import NodeMember

# Mapeo de tipo de nodo a prefijo de código
NODE_TYPE_PREFIX = {
    "sociedad_civil": "A",
    "cientifico": "C",
    "empresarial": "E",
    "funcion_publica": "F",
    "individual": "I",
}

# Inverso: prefijo a tipo
PREFIX_NODE_TYPE = {v: k for k, v in NODE_TYPE_PREFIX.items()}


def generate_node_code(db: Session, node_type: str) -> str:
    """
    Genera el siguiente código de nodo basado en el tipo.
    Ejemplo: sociedad_civil → A01, A02, A03...
    """
    prefix = NODE_TYPE_PREFIX.get(node_type)
    if not prefix:
        raise ValueError(f"Tipo de nodo no válido: {node_type}")

    # Buscar todos los nodos con este prefijo
    existing_codes = (
        db.query(Node.code)
        .filter(Node.code.like(f"{prefix}%"))
        .all()
    )

    max_number = 0
    for (code,) in existing_codes:
        try:
            # Extraer el número del código (ejemplo: A01 → 1, A12 → 12)
            num_part = code[len(prefix):]
            # Solo considerar la parte antes del guión (para no confundir con códigos de miembros)
            if "-" not in num_part:
                num = int(num_part)
                max_number = max(max_number, num)
        except (ValueError, IndexError):
            continue

    next_number = max_number + 1
    return f"{prefix}{next_number:02d}"


def generate_member_code(db: Session, node_code: str) -> str:
    """
    Genera el siguiente código de miembro para un nodo.
    Ejemplo: A01 → A01-1, A01-2, A01-3...
    El líder del nodo tiene como código el del nodo (A01).
    """
    existing_codes = (
        db.query(NodeMember.member_code)
        .filter(NodeMember.member_code.like(f"{node_code}-%"))
        .all()
    )

    max_number = 0
    for (code,) in existing_codes:
        try:
            # Extraer el número después del guión (A01-1 → 1, A01-12 → 12)
            num_part = code.split("-")[-1]
            num = int(num_part)
            max_number = max(max_number, num)
        except (ValueError, IndexError):
            continue

    next_number = max_number + 1
    return f"{node_code}-{next_number}"


def get_prefix_for_type(node_type: str) -> str:
    """Obtiene el prefijo de código para un tipo de nodo."""
    prefix = NODE_TYPE_PREFIX.get(node_type)
    if not prefix:
        raise ValueError(f"Tipo de nodo no válido: {node_type}")
    return prefix
