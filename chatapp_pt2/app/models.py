from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

#adds group members table, unique for every groupchat
group_members = sa.Table(
    "group_members",
    db.metadata,
    sa.Column("user_id", sa.ForeignKey("user.id"), primary_key=True),
    sa.Column("group_id", sa.ForeignKey("group_chat.id"), primary_key=True),
)


class User(UserMixin, db.Model): #adds user table, so.mapped_column adds additional information on datatypes etc.
    id: so.Mapped[int] = so.mapped_column(primary_key=True) 
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    is_online: so.Mapped[bool] = so.mapped_column(default=False)

#add relations with different tables
    sent_messages: so.WriteOnlyMapped["PrivateMessage"] = so.relationship(
        foreign_keys="PrivateMessage.sender_id",
        back_populates="sender",
    )

    received_messages: so.WriteOnlyMapped["PrivateMessage"] = so.relationship(
        foreign_keys="PrivateMessage.receiver_id",
        back_populates="receiver",
    )

    group_messages: so.WriteOnlyMapped["GroupMessage"] = so.relationship(
        back_populates="sender"
    )

    groups: so.Mapped[list["GroupChat"]] = so.relationship(
        secondary=group_members,
        back_populates="members",
    )

    def __repr__(self): #define how to print objects of the User class
        return f"<User {self.username}>"

    def set_password(self, password): #uses Flask password hashing for password
        self.password_hash = generate_password_hash(password)

    def check_password(self, password): #uses Flasks password checker
        return check_password_hash(self.password_hash, password)


class PrivateMessage(db.Model): #add table that saves all private messages
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(500))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True,
        default=lambda: datetime.now(timezone.utc), #lambda function shows current datetime as timestamp
    )

    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True) #references user id
    receiver_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True) #references user id

#add relations with other tables
    sender: so.Mapped[User] = so.relationship(
        foreign_keys=[sender_id],
        back_populates="sent_messages",
    )
    receiver: so.Mapped[User] = so.relationship(
        foreign_keys=[receiver_id],
        back_populates="received_messages",
    )

    def __repr__(self): 
        return f"<PrivateMessage {self.id}>"


class GroupChat(db.Model): # add groupchat info table
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))

#add relations with other tables
    members: so.Mapped[list[User]] = so.relationship(
        secondary=group_members,
        back_populates="groups",
    )

    messages: so.Mapped[list["GroupMessage"]] = so.relationship(
        back_populates="group",
        cascade="all, delete-orphan", #when groupchat is deleted, delete the groupchat messages (weak entity)
    )

    def __repr__(self):
        return f"<GroupChat {self.name}>"


class GroupMessage(db.Model): # add table that saves all group chats
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(500))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True,
        default=lambda: datetime.now(timezone.utc),
    )

#reference user id to show who sent the text
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    group_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(GroupChat.id), index=True)

#add relations with other tables
    sender: so.Mapped[User] = so.relationship(back_populates="group_messages")
    group: so.Mapped[GroupChat] = so.relationship(back_populates="messages")

    def __repr__(self):
        return f"<GroupMessage {self.id}>"


@login.user_loader #convert user id from string to integer
def load_user(id):
    return db.session.get(User, int(id))
