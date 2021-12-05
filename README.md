# ClassicForum 
https://classicforum.herokuapp.com

A discussion forum that serves as a medium for users to create topics, reply to topics and comments, view comment change history and upload images etcetera. With a moderation system that provides a way to convert specific users to moderators.

## Key Features
- Image upload
- In-app notification
- Quote reply
- Comment change history

## Demo Screenshots

![Home Page](https://github.com/successIA/Forum/blob/master/screenshots/screenshot1.png?raw=true)

![Thread Page](https://github.com/successIA/Forum/blob/master/screenshots/screenshot2.png?raw=true)

## Requirement
- python >= 3.6

## Installation
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser --username admin --email a@a.com
python manage.py loaddata category.json
python manage.py runserver
```
