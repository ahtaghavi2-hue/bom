from flask import current_app, render_template
from extensions import db, mail
from models import Part, NotificationLog
from flask_mail import Message
from datetime import datetime

def send_low_stock_email(part):
    if not part.supplier_email:
        return False
    try:
        msg = Message(
            subject=f'هشدار کمبود موجودی: {part.name}',
            recipients=[part.supplier_email],
            html=render_template('modern/email/low_stock.html',
                part_name=part.name,
                part_code=part.part_code or '-',
                current_stock=part.quantity or 0,
                required=part.required_quantity or 1,
                shortage=(part.required_quantity or 1) - (part.quantity or 0)
            )
        )
        mail.send(msg)
        log = NotificationLog(
            part_id=part.id,
            notification_type='email',
            sent_to=part.supplier_email,
            status='sent',
            message=f'هشدار کمبود برای {part.name} ارسال شد'
        )
        db.session.add(log)
        db.session.commit()
        return True
    except Exception as e:
        log = NotificationLog(
            part_id=part.id,
            notification_type='email',
            sent_to=part.supplier_email,
            status='failed',
            message=str(e)
        )
        db.session.add(log)
        db.session.commit()
        current_app.logger.error(f'Email failed for {part.name}: {e}')
        return False

def check_and_notify_low_stock():
    with current_app.app_context():
        low_stock_parts = Part.query.all()
        sent = 0
        for part in low_stock_parts:
            required = part.required_quantity or 1
            available = part.quantity or 0
            if available < required and part.supplier_email:
                if send_low_stock_email(part):
                    sent += 1
        current_app.logger.info(f'Low stock check complete. Sent {sent} notifications.')
