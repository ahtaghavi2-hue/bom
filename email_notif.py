from flask import current_app, render_template
from extensions import db, mail
from models import Part, NotificationLog
from flask_mail import Message
from datetime import datetime

def send_low_stock_email(part, node=None, recipient=None):
    recipient = recipient or part.supplier_email
    if not recipient:
        return False
    if node is None:
        node = current_app.extensions['bom_load_data']()['nodes'].get(f'r{part.id}')
    if not node or node['shortage'] <= 0:
        return False
    try:
        msg = Message(
            subject=f'هشدار کمبود موجودی: {part.name}',
            recipients=[recipient],
            html=render_template('modern/email/low_stock.html',
                part_name=part.name,
                part_code=part.part_code or '-',
                current_stock=node['quantity'],
                required=node['required_total'],
                shortage=node['shortage']
            )
        )
        mail.send(msg)
        log = NotificationLog(
            part_id=part.id,
            notification_type='email',
            sent_to=recipient,
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
            sent_to=recipient,
            status='failed',
            message=str(e)
        )
        db.session.add(log)
        db.session.commit()
        current_app.logger.error(f'Email failed for {part.name}: {e}')
        return False

def check_and_notify_low_stock():
    with current_app.app_context():
        data = current_app.extensions['bom_load_data']()
        low_stock_parts = Part.query.all()
        sent = 0
        for part in low_stock_parts:
            node = data['nodes'].get(f'r{part.id}')
            if node and node['shortage'] > 0 and part.supplier_email:
                if send_low_stock_email(part, node=node):
                    sent += 1
        current_app.logger.info(f'Low stock check complete. Sent {sent} notifications.')
