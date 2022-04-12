FROM python:3.9
WORKDIR /home/

COPY requirements.txt /home/
RUN pip install -r requirements.txt
COPY . /home/

RUN python manage.py compilemessages -i "venv" -i LICENSE.txt
CMD ["gunicorn", "shadowmere.wsgi:application", "--bind", "0.0.0.0:8001", "-k", "gevent", "-w", "6"]
