import logging
from typing import Any, Dict, List

logger = logging.getLogger("taskhub.notifications")

# In-memory store dung cho dev va testing
sent_notifications: List[Dict[str, Any]] = []


def send_task_assignment_email(
    to_email: str,
    recipient_name: str,
    task_title: str,
    task_id: int,
) -> None:
    """Gui email thong bao khi user duoc assign vao task (chay bang BackgroundTasks)."""
    subject = f"[TaskHub] Ban duoc giao task moi: {task_title}"
    body = (
        f"Xin chao {recipient_name},\n\n"
        f"Ban vua duoc assign vao task '{task_title}' (Task ID: #{task_id}).\n"
        f"Vui long dang nhap he thong TaskHub de xem chi tiet va cap nhat tien do.\n\n"
        f"Tran trong,\n"
        f"TaskHub Team"
    )

    logger.info("Gui email thong bao den %s ve task #%d (%s)", to_email, task_id, task_title)

    notification_record = {
        "to_email": to_email,
        "recipient_name": recipient_name,
        "task_id": task_id,
        "task_title": task_title,
        "subject": subject,
        "body": body,
    }
    sent_notifications.append(notification_record)
