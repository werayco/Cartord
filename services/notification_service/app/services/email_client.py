from email.message import EmailMessage
from typing import Literal, Optional
import aiosmtplib
import resend
from app.core.config import settings

EmailProvider = Literal["resend", "smtp", "mailpit"]

class EmailService:
    def __init__(self, provider: Optional[EmailProvider] = None, *, resend_api_key: Optional[str] = None, smtp_host: Optional[str] = None, smtp_port: Optional[int] = None, smtp_username: Optional[str] = None, smtp_password: Optional[str] = None, smtp_use_tls: Optional[bool] = None, mailpit_host: Optional[str] = None, mailpit_port: Optional[int] = None):
        self.provider = provider or settings.EMAIL_PROVIDER
        self.resend_api_key = resend_api_key or settings.RESEND_API_KEY
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.smtp_username = smtp_username or settings.SMTP_USERNAME
        self.smtp_password = smtp_password or settings.SMTP_PASSWORD
        self.smtp_use_tls = smtp_use_tls if smtp_use_tls is not None else settings.SMTP_USE_TLS
        self.mailpit_host = mailpit_host or settings.MAILPIT_HOST
        self.mailpit_port = mailpit_port or settings.MAILPIT_PORT

    async def send_email(self, *, to: str, subject: str, html_body: str, from_email: str, from_name: Optional[str] = None) -> None:
        if self.provider == "resend":
            await self._send_with_resend(to=to, subject=subject, html_body=html_body, from_email=from_email, from_name=from_name, resend_api_key=self.resend_api_key)
        elif self.provider == "smtp":
            await self._send_with_smtp(to=to, subject=subject, html_body=html_body, from_email=from_email, from_name=from_name, smtp_host=self.smtp_host, smtp_port=self.smtp_port, smtp_username=self.smtp_username, smtp_password=self.smtp_password, smtp_use_tls=self.smtp_use_tls)
        elif self.provider == "mailpit":
            await self._send_with_mailpit(to=to, subject=subject, html_body=html_body, from_email=from_email, from_name=from_name, mailpit_host=self.mailpit_host, mailpit_port=self.mailpit_port)
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")

    @staticmethod
    async def _send_with_resend(*, to: str, subject: str, html_body: str, from_email: str, from_name: Optional[str], resend_api_key: str) -> None:
        resend.api_key = resend_api_key
        sender = f"{from_name} <{from_email}>" if from_name else from_email
        resend.Emails.send({"from": sender, "to": [to], "subject": subject, "html": html_body})

    @staticmethod
    async def _send_with_smtp(*, to: str, subject: str, html_body: str, from_email: str, from_name: Optional[str], smtp_host: str, smtp_port: int, smtp_username: str, smtp_password: str, smtp_use_tls: bool = True) -> None:
        msg = EmailMessage()
        msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.add_alternative(html_body, subtype="html")
        await aiosmtplib.send(msg, hostname=smtp_host, port=smtp_port, username=smtp_username, password=smtp_password, start_tls=smtp_use_tls)

    @staticmethod
    async def _send_with_mailpit(*, to: str, subject: str, html_body: str, from_email: str, from_name: Optional[str], mailpit_host: str, mailpit_port: int) -> None:
        msg = EmailMessage()
        msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.add_alternative(html_body, subtype="html")
        await aiosmtplib.send(msg, hostname=mailpit_host, port=mailpit_port)

email_service = EmailService(provider="smtp")