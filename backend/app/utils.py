import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    assert settings.emails_enabled, "no provided configuration for email variables"
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"send email result: {response}")


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None


# ==================== 文件上传工具函数 ====================

def save_upload_file(
    *,
    file_content: bytes,
    filename: str,
    subfolder: str = "",
) -> str:
    """
    保存上传的文件到上传目录

    Args:
        file_content: 文件内容（字节）
        filename: 原始文件名
        subfolder: 子文件夹（如 contracts, invoices）

    Returns:
        保存后的文件相对路径
    """
    # 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    if subfolder:
        upload_dir = upload_dir / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一的文件名（保留原始扩展名）
    ext = Path(filename).suffix.lower().lstrip(".")
    allowed_extensions = {value.lstrip(".") for value in settings.ALLOWED_EXTENSIONS}
    if ext not in allowed_extensions:
        raise ValueError(f"不支持的文件类型: .{ext}")
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / unique_filename

    # 保存文件
    file_path.write_bytes(file_content)

    # 返回相对路径
    relative_path = file_path.relative_to(Path(settings.UPLOAD_DIR))
    return str(relative_path)


def delete_file(file_path: str) -> bool:
    """
    删除文件

    Args:
        file_path: 文件相对路径

    Returns:
        是否成功删除
    """
    try:
        full_path = Path(settings.UPLOAD_DIR) / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_url(file_path: str) -> str:
    """
    获取文件的访问URL

    Args:
        file_path: 文件相对路径

    Returns:
        文件的访问URL
    """
    # 这里可以根据实际情况调整，返回静态文件服务URL
    return f"/api/v1/files/{file_path}"
