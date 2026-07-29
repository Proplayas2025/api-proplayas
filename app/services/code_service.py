"""Generación de códigos de nodo (A01) y de miembro (A01-1)."""
from fastapi import HTTPException

from repositories.node_member_repository import NodeMemberRepository
from repositories.node_repository import NodeRepository

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


class CodeService:
    def __init__(self, nodes: NodeRepository, memberships: NodeMemberRepository):
        self.nodes = nodes
        self.memberships = memberships

    def prefix_for_type(self, node_type: str) -> str:
        """Prefijo de código para un tipo de nodo."""
        prefix = NODE_TYPE_PREFIX.get(node_type)
        if not prefix:
            raise HTTPException(status_code=400, detail=f"Tipo de nodo no válido: {node_type}")
        return prefix

    def generate_node_code(self, node_type: str) -> str:
        """Siguiente código de nodo según el tipo. Ej: sociedad_civil → A01, A02..."""
        prefix = self.prefix_for_type(node_type)

        max_number = 0
        for code in self.nodes.list_codes_with_prefix(prefix):
            # Ignorar códigos de miembro (llevan guión) para no confundir la numeración
            num_part = code[len(prefix):]
            if "-" in num_part:
                continue
            try:
                max_number = max(max_number, int(num_part))
            except ValueError:
                continue

        return f"{prefix}{max_number + 1:02d}"

    def generate_member_code(self, node_code: str) -> str:
        """Siguiente código de miembro del nodo. Ej: A01 → A01-1, A01-2...

        El líder del nodo usa como código el del propio nodo (A01).
        """
        max_number = 0
        for code in self.memberships.list_member_codes(node_code):
            try:
                max_number = max(max_number, int(code.split("-")[-1]))
            except ValueError:
                continue

        return f"{node_code}-{max_number + 1}"
