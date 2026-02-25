import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
 
from config.config import settings
 
conf = ConnectionConfig(
    MAIL_USERNAME = settings.EMAIL_ADDRESS,
    MAIL_PASSWORD = settings.EMAIL_PASSWORD,
    MAIL_FROM = settings.EMAIL_ADDRESS,
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)
 
async def send_task_completion_email(email_to: str, task_name: str):
    html = f"""
    <p>Hello,</p>
    <p>The task <strong>{task_name}</strong> has been marked as <strong>Completed</strong>.</p>
    <p>Check your dashboard for details.</p>
    """
 
    message = MessageSchema(
        subject="Task Completed Notification",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )
 
    fm = FastMail(conf)
    await fm.send_message(message)
async def send_invite_email(email_to: str, team_name: str, invite_token: str):
    html = f"""
    <p>Hello,</p>

    <p>You have been invited to join the team 
    <strong>{team_name}</strong>.</p>

    <p>Please use the invite token below to accept the invitation:</p>

    <div style="padding:10px; background-color:#f4f4f4; border-radius:5px; font-size:16px;">
        <strong>{invite_token}</strong>
    </div>

    <p>This invite will expire in 24 hours.</p>

    <p>If you did not expect this invitation, you can ignore this email.</p>

    <br>
    <p>Regards,<br>
    Team Management System</p>
    """

    message = MessageSchema(
        subject="Team Invitation",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)