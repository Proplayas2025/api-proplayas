import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL or self.smtp_user or "noreply@proplayas.org"
        self.from_name = settings.FROM_NAME
        self.frontend_url = settings.FRONTEND_URL
        self.environment = getattr(settings, "ENVIRONMENT", "development")
        
        logger.info(f"EmailService initialized - Host: {self.smtp_host}:{self.smtp_port}, Environment: {self.environment}")
    
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
            
            # En desarrollo (MailHog) no requiere autenticación ni TLS
            if self.environment == "development" or not self.smtp_user:
                logger.info(f"Sending email to {to_email} via {self.smtp_host}:{self.smtp_port} (no auth)")
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    timeout=10
                )
            else:
                # Producción: con autenticación
                logger.info(f"Sending email to {to_email} via {self.smtp_host}:{self.smtp_port} (with auth)")
                if self.smtp_port == 465:
                    await aiosmtplib.send(
                        message,
                        hostname=self.smtp_host,
                        port=self.smtp_port,
                        username=self.smtp_user,
                        password=self.smtp_password,
                        use_tls=True,
                        timeout=10
                    )
                else:
                    await aiosmtplib.send(
                        message,
                        hostname=self.smtp_host,
                        port=self.smtp_port,
                        username=self.smtp_user,
                        password=self.smtp_password,
                        start_tls=True,
                        timeout=10
                    )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}", exc_info=True)
            return False
    
    async def send_invitation_email(self, to_email: str, invitation_token: str, role: str) -> bool:
        """
        Envía un email de invitación con el token.
        role puede ser: 'node_leader' o 'member'
        """
        role_names = {
            "node_leader": "Líder de Nodo",
            "member": "Miembro de Nodo"
        }
        role_display = role_names.get(role, role)
        
        invitation_url = f"{self.frontend_url}/validate-invitation?token={invitation_token}"
        
        subject = f"Invitación a Proplayas - {role_display}"
        
        html_content = self._get_invitation_template(
            role_display=role_display,
            invitation_url=invitation_url,
            role_type=role
        )
        
        plain_content = f"""
Has sido invitado a unirte a la Red Proplayas como {role_display}.

Para completar tu registro, visita el siguiente enlace:
{invitation_url}

Este enlace es válido por 7 días.

Si no solicitaste esta invitación, puedes ignorar este correo.

---
Red Proplayas
Conservación de playas y ecosistemas costeros
        """.strip()
        
        return await self.send_email(to_email, subject, html_content, plain_content)
    
    def _get_invitation_template(self, role_display: str, invitation_url: str, role_type: str) -> str:
        """Plantilla HTML profesional para invitaciones"""
        
        # Mensaje personalizado según el rol
        if role_type == "node_leader":
            intro_text = """
            Has sido invitado a liderar un nuevo nodo en la Red Proplayas. 
            Como líder de nodo, podrás gestionar miembros, crear contenido y 
            representar a tu organización en nuestra red de conservación marina.
            """
        else:
            intro_text = """
            Has sido invitado a unirte como miembro de un nodo en la Red Proplayas.
            Como miembro, podrás colaborar en proyectos, compartir investigaciones
            y contribuir a la conservación de nuestros ecosistemas costeros.
            """
        
        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invitación a Proplayas</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold;">
                                Proplayas
                            </h1>
                            <p style="color: #e0f2fe; margin: 10px 0 0 0; font-size: 14px;">
                                Red de Conservación de Playas y Ecosistemas Costeros
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #0891b2; margin: 0 0 20px 0; font-size: 24px;">
                                ¡Has sido invitado!
                            </h2>
                            
                            <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 15px 0;">
                                Hola,
                            </p>
                            
                            <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 15px 0;">
                                {intro_text}
                            </p>
                            
                            <div style="background-color: #f0f9ff; border-left: 4px solid #0891b2; padding: 15px; margin: 25px 0;">
                                <p style="color: #0c4a6e; margin: 0; font-size: 14px;">
                                    <strong>Tu rol:</strong> {role_display}
                                </p>
                            </div>
                            
                            <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                                Para completar tu registro y unirte a la red, haz clic en el siguiente botón:
                            </p>
                            
                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{invitation_url}" 
                                           style="display: inline-block; background-color: #0891b2; color: #ffffff; 
                                                  text-decoration: none; padding: 15px 40px; border-radius: 6px; 
                                                  font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(8, 145, 178, 0.3);">
                                            Completar Registro
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #666666; font-size: 14px; line-height: 1.5; margin: 20px 0 0 0;">
                                O copia y pega este enlace en tu navegador:
                            </p>
                            <p style="color: #0891b2; font-size: 14px; word-break: break-all; margin: 5px 0 20px 0;">
                                {invitation_url}
                            </p>
                            
                            <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 30px;">
                                <p style="color: #999999; font-size: 13px; line-height: 1.5; margin: 0;">
                                    <strong>⏰ Este enlace es válido por 7 días.</strong>
                                </p>
                                <p style="color: #999999; font-size: 13px; line-height: 1.5; margin: 10px 0 0 0;">
                                    Si no solicitaste esta invitación, puedes ignorar este correo de forma segura.
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="color: #64748b; font-size: 14px; margin: 0 0 10px 0;">
                                <strong>Red Proplayas</strong>
                            </p>
                            <p style="color: #94a3b8; font-size: 12px; line-height: 1.5; margin: 0;">
                                Conservación de playas y ecosistemas costeros<br>
                                <a href="{self.frontend_url}" style="color: #0891b2; text-decoration: none;">
                                    www.proplayas.org
                                </a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """.strip()

email_service = EmailService()
