Chatbot for MTFood Project

To install you must have:

- python 3.4 - 3.9
- pip

Create virtual environment:

- python -m venv ./venv

Run virtual environment:

- .\venv\Scripts\activate

Install rasa:

- pip install rasa

Run rasa action server:

- rasa run actions

Rasa servers will be available at port http:localhost/5055

Run rasa server:

- rasa run --enable-api --cors "\*"
