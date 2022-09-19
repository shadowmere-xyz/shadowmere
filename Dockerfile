FROM python:3.10-alpine
WORKDIR /home/

ENV APP_HOME=/home/
ENV APP_USER=shadowmere
ENV APP_GROUP=shadowmeregroup
RUN addgroup -S $APP_GROUP && adduser -H -S $APP_USER -G $APP_GROUP -s /sbin/nologin

RUN apk --no-cache add gcc musl-dev libffi-dev openssl-dev python3-dev g++
RUN pip install --upgrade pip

COPY requirements.txt /home/
RUN pip install -r requirements.txt
COPY . /home/

RUN chown -R $APP_USER:$APP_GROUP $APP_HOME
USER $APP_USER

CMD ["gunicorn", "shadowmere.wsgi:application", "--bind", "0.0.0.0:8001", "-k", "gevent", "-w", "6", "--capture-output"]
