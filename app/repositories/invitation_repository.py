from enums import InvitationStatus, UserRole
from models.invitation import Invitation
from repositories.base import BaseRepository


class InvitationRepository(BaseRepository[Invitation]):
    model = Invitation

    def get_pending_by_email(self, email: str) -> Invitation | None:
        return (
            self.db.query(Invitation)
            .filter(
                Invitation.email == email,
                Invitation.status == InvitationStatus.pending,
            )
            .first()
        )

    def get_pending_by_token(self, token: str) -> Invitation | None:
        return (
            self.db.query(Invitation)
            .filter(
                Invitation.token == token,
                Invitation.status == InvitationStatus.pending,
            )
            .first()
        )

    def list_by_status(
        self,
        status: InvitationStatus,
        *,
        role: UserRole | None = None,
        invited_by: int | None = None,
    ) -> list[Invitation]:
        query = self.db.query(Invitation).filter(Invitation.status == status)

        if role is not None:
            query = query.filter(Invitation.role == role)

        if invited_by is not None:
            query = query.filter(Invitation.invited_by == invited_by)

        return query.order_by(Invitation.created_at.desc()).all()
