from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from sqlalchemy import or_, and_
from flask_socketio import emit

from app import app, db, socketio
from app.forms import (
    LoginForm,
    RegistrationForm,
    PrivateMessageForm,
    GroupChatForm,
    GroupMessageForm
)
from app.models import User, PrivateMessage, GroupChat, GroupMessage


# Zet User om naar dict
def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "is_online": user.is_online
    }


# Zet private message om naar dict
def private_message_to_dict(message):
    return {
        "id": message.id,
        "body": message.body,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "sender_username": message.sender.username,
        "receiver_username": message.receiver.username,
        "timestamp": message.timestamp.isoformat()
    }


# Zet group om naar dict
def group_to_dict(group):
    return {
        "id": group.id,
        "name": group.name,
        "members": [
            {"id": m.id, "username": m.username}
            for m in group.members
        ]
    }


# Zet group message om naar dict
def group_message_to_dict(message):
    return {
        "id": message.id,
        "body": message.body,
        "sender_id": message.sender_id,
        "sender_username": message.sender.username,
        "group_id": message.group_id,
        "timestamp": message.timestamp.isoformat()
    }


@app.route("/")
def home():
    # Redirect afhankelijk van login status
    if current_user.is_authenticated:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # Als al ingelogd, direct naar chat
    if current_user.is_authenticated:
        return redirect(url_for("chat"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )

        # Check login gegevens
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))

        login_user(user)
        user.is_online = True
        db.session.commit()

        return redirect(url_for("chat"))

    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
@login_required
def logout():
    # Zet user offline en log uit
    current_user.is_online = False
    db.session.commit()
    logout_user()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # Als al ingelogd, geen registratie
    if current_user.is_authenticated:
        return redirect(url_for("chat"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check of username al bestaat
        existing_user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if existing_user is not None:
            flash("Username is already in use.")
            return redirect(url_for("register"))

        # Simpele password check
        if len(form.password.data) < 8:
            flash("Password must be at least 8 characters long.")
            return redirect(url_for("register"))

        user = User(username=form.username.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Your account has been created.")
        return redirect(url_for("login"))

    return render_template("register.html", title="Register", form=form)


@app.route("/chat", methods=["GET"])
@login_required
def chat():
    # Geselecteerde chat (user of group)
    selected_user_id = request.args.get("user_id", type=int)
    selected_group_id = request.args.get("group_id", type=int)

    # Online users behalve jezelf
    active_users = db.session.scalars(
        sa.select(User).where(
            User.id != current_user.id,
            User.is_online == True
        ).order_by(User.username)
    ).all()

    groups = current_user.groups

    # Forms
    private_form = PrivateMessageForm()
    group_form = GroupChatForm()
    group_message_form = GroupMessageForm()

    # Members voor nieuwe group
    all_other_users = db.session.scalars(
        sa.select(User).where(User.id != current_user.id).order_by(User.username)
    ).all()
    group_form.members.choices = [(u.id, u.username) for u in all_other_users]

    private_messages = []
    group_messages = []

    selected_user = None
    selected_group = None

    # Private chat laden
    if selected_user_id is not None:
        selected_user = db.session.get(User, selected_user_id)

        if selected_user is None or selected_user.id == current_user.id:
            flash("Invalid user.")
            return redirect(url_for("chat"))

        private_messages = db.session.scalars(
            sa.select(PrivateMessage)
            .where(
                or_(
                    and_(
                        PrivateMessage.sender_id == current_user.id,
                        PrivateMessage.receiver_id == selected_user.id
                    ),
                    and_(
                        PrivateMessage.sender_id == selected_user.id,
                        PrivateMessage.receiver_id == current_user.id
                    )
                )
            )
            .order_by(PrivateMessage.timestamp.asc())
        ).all()

    # Group chat laden
    if selected_group_id is not None:
        selected_group = db.session.get(GroupChat, selected_group_id)

        if selected_group is None or current_user not in selected_group.members:
            flash("Access denied.")
            return redirect(url_for("chat"))

        group_messages = db.session.scalars(
            sa.select(GroupMessage)
            .where(GroupMessage.group_id == selected_group.id)
            .order_by(GroupMessage.timestamp.asc())
        ).all()

    return render_template(
        "chat.html",
        title="Chat",
        active_users=active_users,
        groups=groups,
        selected_user=selected_user,
        selected_group=selected_group,
        private_messages=private_messages,
        group_messages=group_messages,
        private_form=private_form,
        group_form=group_form,
        group_message_form=group_message_form
    )


@app.route("/send_message/<int:user_id>", methods=["POST"])
@login_required
def send_message(user_id):
    #sla bericht op in database
    other_user = db.session.get(User, user_id)
    if other_user is None or other_user.id == current_user.id:
        flash("Invalid user.")
        return redirect(url_for("chat"))

    form = PrivateMessageForm()
    if form.validate_on_submit():
        message = PrivateMessage(
            body=form.body.data,
            sender_id=current_user.id,
            receiver_id=other_user.id
        )
        db.session.add(message)
        db.session.commit()

        #verstuur bericht via websockets
        payload = private_message_to_dict(message)
        socketio.emit('new_private_message', payload, to=f'user_{current_user.id}')
        socketio.emit('new_private_message', payload, to=f'user_{other_user.id}')

    return redirect(url_for("chat", user_id=user_id))


@app.route("/create_group", methods=["POST"])
@login_required
def create_group():
    # Maak nieuwe group
    form = GroupChatForm()

    all_other_users = db.session.scalars(
        sa.select(User).where(User.id != current_user.id).order_by(User.username)
    ).all()
    form.members.choices = [(u.id, u.username) for u in all_other_users]

    if form.validate_on_submit():
        selected_members = db.session.scalars(
            sa.select(User).where(User.id.in_(form.members.data))
        ).all()

        # Minimaal 3 users (incl jezelf)
        if len(selected_members) < 2:
            flash("A group must contain at least 3 users including yourself.")
            return redirect(url_for("chat"))

        group = GroupChat(name=form.name.data)
        group.members.append(current_user)

        for member in selected_members:
            if member not in group.members:
                group.members.append(member)

        db.session.add(group)
        db.session.commit()

        return redirect(url_for("chat", group_id=group.id))

    flash("Could not create group.")
    return redirect(url_for("chat"))


@app.route("/send_group_message/<int:group_id>", methods=["POST"])
@login_required
def send_group_message(group_id):
    # sla groupschat op in database
    group = db.session.get(GroupChat, group_id)

    if group is None or current_user not in group.members:
        flash("Access denied.")
        return redirect(url_for("chat"))

    form = GroupMessageForm()
    if form.validate_on_submit():
        message = GroupMessage(
            body=form.body.data,
            sender_id=current_user.id,
            group_id=group.id
        )
        db.session.add(message)
        db.session.commit()
    
        #verstuur de groupschat via websockets
        socketio.emit('new_group_message', group_message_to_dict(message), to=f'group_{group.id}')


    return redirect(url_for("chat", group_id=group_id))


# API endpoints

@app.route("/api/login", methods=["POST"])
def api_login():
    # Login via API
    if current_user.is_authenticated:
        return jsonify({"message": "Already logged in"}), 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = db.session.scalar(
        sa.select(User).where(User.username == username)
    )

    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    login_user(user)
    user.is_online = True
    db.session.commit()

    return jsonify({
        "message": "Login successful",
        "user": user_to_dict(user)
    }), 200


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    # Logout via API
    current_user.is_online = False
    db.session.commit()
    logout_user()
    return jsonify({"message": "Logout successful"}), 200


@app.route("/api/register", methods=["POST"])
def api_register():
    # Registratie via API
    if current_user.is_authenticated:
        return jsonify({"error": "Logout before registering a new account"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    existing_user = db.session.scalar(
        sa.select(User).where(User.username == username)
    )
    if existing_user is not None:
        return jsonify({"error": "Username is already in use"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    user = User(username=username)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Account created successfully",
        "user": user_to_dict(user)
    }), 201


@app.route("/api/active_users", methods=["GET"])
@login_required
def api_active_users():
    # Geef online users terug
    users = db.session.scalars(
        sa.select(User).where(
            User.id != current_user.id,
            User.is_online == True
        ).order_by(User.username)
    ).all()

    return jsonify([user_to_dict(u) for u in users]), 200


@app.route("/api/groups", methods=["GET"])
@login_required
def api_groups():
    # Groups van huidige user
    return jsonify([group_to_dict(g) for g in current_user.groups]), 200


@app.route("/api/groups", methods=["POST"])
@login_required
def api_create_group():
    # Maak group via API
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    name = data.get("name", "").strip()
    member_ids = data.get("member_ids", [])

    if not name:
        return jsonify({"error": "Group name is required"}), 400

    if not isinstance(member_ids, list):
        return jsonify({"error": "member_ids must be a list"}), 400

    selected_members = db.session.scalars(
        sa.select(User).where(User.id.in_(member_ids))
    ).all()

    if len(selected_members) < 2:
        return jsonify({
            "error": "A group must contain at least 3 users including yourself"
        }), 400

    group = GroupChat(name=name)
    group.members.append(current_user)

    for member in selected_members:
        if member.id != current_user.id and member not in group.members:
            group.members.append(member)

    db.session.add(group)
    db.session.commit()

    return jsonify({
        "message": "Group created successfully",
        "group": group_to_dict(group)
    }), 201


@app.route("/api/private_messages/<int:user_id>", methods=["GET"])
@login_required
def api_get_private_messages(user_id):
    # Haal private messages op
    other_user = db.session.get(User, user_id)

    if other_user is None or other_user.id == current_user.id:
        return jsonify({"error": "Invalid user"}), 400

    messages = db.session.scalars(
        sa.select(PrivateMessage)
        .where(
            or_(
                and_(
                    PrivateMessage.sender_id == current_user.id,
                    PrivateMessage.receiver_id == other_user.id
                ),
                and_(
                    PrivateMessage.sender_id == other_user.id,
                    PrivateMessage.receiver_id == current_user.id
                )
            )
        )
        .order_by(PrivateMessage.timestamp.asc())
    ).all()

    return jsonify([private_message_to_dict(m) for m in messages]), 200


@app.route("/api/private_messages/<int:user_id>", methods=["POST"])
@login_required
def api_send_private_message(user_id):
    # sla private message op in database via API
    other_user = db.session.get(User, user_id)

    if other_user is None or other_user.id == current_user.id:
        return jsonify({"error": "Invalid user"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    body = data.get("body", "").strip()
    if not body:
        return jsonify({"error": "Message cannot be empty"}), 400

    message = PrivateMessage(
        body=body,
        sender_id=current_user.id,
        receiver_id=other_user.id
    )
    db.session.add(message)
    db.session.commit()

    #versturen via de sockets
    payload = private_message_to_dict(message)
    socketio.emit('new_private_message', payload, to=f'user_{current_user.id}')
    socketio.emit('new_private_message', payload, to=f'user_{other_user.id}')

    return jsonify({
        "message": "Private message sent successfully",
        "private_message": private_message_to_dict(message)
    }), 201


@app.route("/api/group_messages/<int:group_id>", methods=["GET"])
@login_required
def api_get_group_messages(group_id):
    # Haal group messages op
    group = db.session.get(GroupChat, group_id)

    if group is None:
        return jsonify({"error": "Group not found"}), 404

    if current_user not in group.members:
        return jsonify({"error": "Access denied"}), 403

    messages = db.session.scalars(
        sa.select(GroupMessage)
        .where(GroupMessage.group_id == group.id)
        .order_by(GroupMessage.timestamp.asc())
    ).all()

    return jsonify([group_message_to_dict(m) for m in messages]), 200


@app.route("/api/group_messages/<int:group_id>", methods=["POST"])
@login_required
def api_send_group_message(group_id):
    # sla een groupchat op in de database via API
    group = db.session.get(GroupChat, group_id)

    if group is None:
        return jsonify({"error": "Group not found"}), 404

    if current_user not in group.members:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    body = data.get("body", "").strip()
    if not body:
        return jsonify({"error": "Message cannot be empty"}), 400

    message = GroupMessage(
        body=body,
        sender_id=current_user.id,
        group_id=group.id
    )
    db.session.add(message)
    db.session.commit()

    #versturen via socket
    socketio.emit('new_group_message', group_message_to_dict(message), to=f'group_{group.id}')

    return jsonify({
        "message": "Group message sent successfully",
        "group_message": group_message_to_dict(message)
    }), 201
