from email.message import EmailMessage
from typing import Literal, Optional
import aiosmtplib
import resend

EmailProvider = Literal["resend", "smtp", "mailpit"]

class EmailService:
    def __init__(self, provider: EmailProvider, *, resend_api_key: Optional[str] = None, smtp_host: Optional[str] = None, smtp_port: Optional[int] = None, smtp_username: Optional[str] = None, smtp_password: Optional[str] = None, smtp_use_tls: bool = True, mailpit_host: str = "mailpit", mailpit_port: int = 1025):
        self.provider = provider
        self.resend_api_key = resend_api_key
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.mailpit_host = mailpit_host
        self.mailpit_port = mailpit_port

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
        
# email_service = EmailService(
#     provider="resend",
#     resend_api_key="your_resend_api_key"
# )

# email_service = EmailService(
#     provider="smtp",
#     smtp_host="smtp.gmail.com",
#     smtp_port=587,
#     smtp_username="your_email@gmail.com",
#     smtp_password="your_password",
#     smtp_use_tls=True
# )

# email_service = EmailService(
#     provider="mailpit",
#     mailpit_host="mailpit",
#     mailpit_port=1025
# )

# await email_service.send_email(
#     to="recipient@example.com",
#     subject="Hello",
#     html_body="<h1>Hello World</h1>",
#     from_email="sender@example.com",
#     from_name="Sender Name"
# )