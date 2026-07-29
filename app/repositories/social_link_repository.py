from enums import SocialPlatform
from models.social_link import NodeSocialLink, SocialLink
from repositories.base import BaseRepository


class SocialLinkRepository(BaseRepository[SocialLink]):
    """Acceso a las redes sociales de usuarios (`SocialLink`) y nodos (`NodeSocialLink`)."""

    model = SocialLink

    # ── Usuario ──
    def delete_by_user(self, user_id: int) -> None:
        self.db.query(SocialLink).filter(SocialLink.user_id == user_id).delete()

    def create_for_user(self, user_id: int, platform: SocialPlatform, url: str) -> SocialLink:
        link = SocialLink(platform=platform, url=url, user_id=user_id)
        self.db.add(link)
        return link

    # ── Nodo ──
    def delete_by_node(self, node_id: int) -> None:
        self.db.query(NodeSocialLink).filter(NodeSocialLink.node_id == node_id).delete()

    def create_for_node(self, node_id: int, platform: SocialPlatform, url: str) -> NodeSocialLink:
        link = NodeSocialLink(platform=platform, url=url, node_id=node_id)
        self.db.add(link)
        return link
