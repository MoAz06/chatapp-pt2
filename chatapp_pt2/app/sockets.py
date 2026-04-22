from flask_login import current_user
from flask_socketio import join_room, leave_room

from app import socketio, db

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        # Elke gebruiker joint een unieke room, met als naam zijn/haar user-id.
        # Hierdoor kan de server berichten sturen naar specifieke gebruikers.
        join_room(f'user_{current_user.id}')

        # Join ook de groepschats waar de gebruiker lid van is
        for group in current_user.groups:
            join_room(f'group_{group.id}')

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')
        for group in current_user.groups:
            leave_room(f'group_{group.id}')
