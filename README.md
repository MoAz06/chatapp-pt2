# Flask Chat Application (PT2)

A web-based chat application built with Flask. This project includes user authentication and real-time messaging using WebSockets.

## Features

- User registration and login
- Secure authentication with session management
- Real-time chat using WebSockets (Flask-SocketIO)
- Multiple users can communicate simultaneously
- Structured Flask backend (routes, models, forms, templates)

## Tech Stack

- Python
- Flask
- Flask-WTF (forms & validation)
- Flask-Login (authentication)
- Flask-SocketIO (real-time communication)
- Jinja2 (templating)
- SQLite (or configured database)

## Project Structure

chatapp_pt2/
│── app/
│   ├── routes.py
│   ├── models.py
│   ├── forms.py
│   ├── templates/
│   └── static/
│── migrations/
│── config.py
│── run.py

## Installation

1. Clone the repository:
git clone https://github.com/MoAz06/chatapp-pt2.git
cd chatapp-pt2

2. Create a virtual environment:
python3 -m venv venv
source venv/bin/activate

3. Install dependencies:
pip install -r requirements.txt

4. Run the application:
flask run

## Usage

- Register a new account
- Log in to the application
- Start chatting in real-time with other users

## Notes

This project was developed as part of the university course Programmeertechnieken.  
The base application was extended with real-time chat functionality using WebSockets.

## Future Improvements

- Private messaging
- Message history persistence
- UI/UX improvements
- Deployment (e.g. Railway or Docker)

## Author

Mohamed Azahrioui

## Notes

This project was originally developed in a private university GitLab environment (LIACS).  
The commit history here is limited because the project was later migrated to GitHub.

The focus of this repository is to showcase the final implementation and functionality.

## Screenshots

### Real-time chat

![Chat Demo](screenshots/chat-demo.png)
