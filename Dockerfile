FROM python:3.9
WORKDIR /home/

COPY requirements.txt /home/
RUN pip install -r requirements.txt
COPY . /home/

CMD ["gunicorn", "shadowmere.wsgi:application", "--bind", "0.0.0.0:8001", "-k", "gevent", "-w", "6"]
