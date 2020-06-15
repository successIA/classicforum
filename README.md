# ClassicForum
Visit https://classicforum.herokuapp.com

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
