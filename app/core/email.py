import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from core.config import settings

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL or self.smtp_user
        self.from_name = settings.FROM_NAME
        self.frontend_url = settings.FRONTEND_URL
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            if plain_content:
                part1 = MIMEText(plain_content, "plain")
                message.attach(part1)
            
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            if self.smtp_user and self.smtp_password:
                if self.smtp_port == 465:
                    await aiosmtplib.send(
                        message,
                        hostname=self.smtp_host,
                        port=self.smtp_port,
                        username=self.smtp_user,
                        password=self.smtp_password,
                        use_tls=True
                    )
                else:
                    await aiosmtplib.send(
                        message,
                        hostname=self.smtp_host,
                        port=self.smtp_port,
                        username=self.smtp_user,
                        password=self.smtp_password,
                        start_tls=True
                    )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port
                )
            
            return True
            
        except Exception as e:
            print(f"Error al enviar email: {e}")
            return False
    
    async def send_invitation_email(self, to_email: str, invitation_token: str, role: str) -> bool:
        subject = f"Invitación a Proplayas como {role}"
        html_content = f"""
        <html>
            <body>
                <h2>Has sido invitado a unirte a Proplayas</h2>
                <p>Has recibido una invitación para registrarte como <strong>{role}</strong>.</p>
                <p>Haz clic en el siguiente enlace para completar tu registro:</p>
                <a href="{self.frontend_url}/validate-invitation?token={invitation_token}">
                    Completar registro
                </a>
                <p>Este enlace es válido por 7 días.</p>
            </body>
        </html>
        """
        plain_content = f"Has sido invitado a unirte a Proplayas como {role}. Visita: {self.frontend_url}/validate-invitation?token={invitation_token}"
        
        return await self.send_email(to_email, subject, html_content, plain_content)

email_service = EmailService()
