from models.node_member import NodeMember
from models.user import User
from repositories.base import BaseRepository


class NodeMemberRepository(BaseRepository[NodeMember]):
    model = NodeMember

    def list_with_users(self, node_id: int) -> list[tuple[NodeMember, User]]:
        """Membresías del nodo junto al usuario asociado."""
        return (
            self.db.query(NodeMember, User)
            .join(User, NodeMember.user_id == User.id)
            .filter(NodeMember.node_id == node_id)
            .all()
        )

    def delete_membership(self, user_id: int, node_id: int) -> None:
        self.db.query(NodeMember).filter(
            NodeMember.user_id == user_id,
            NodeMember.node_id == node_id,
        ).delete()

    def list_member_codes(self, node_code: str) -> list[str]:
        """Códigos de miembro de un nodo (ej. 'A01' → A01-1, A01-2...)."""
        rows = (
            self.db.query(NodeMember.member_code)
            .filter(NodeMember.member_code.like(f"{node_code}-%"))
            .all()
        )
        return [code for (code,) in rows]
