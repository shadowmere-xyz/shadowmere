FROM python:3.10
WORKDIR /home/

ENV APP_HOME=/home/
ENV APP_USER=shadowmere

RUN groupadd -r $APP_USER && \
    useradd -r -g $APP_USER -d $APP_HOME -s /sbin/nologin -c "Docker image user" $APP_USER
RUN pip install --upgrade pip

COPY requirements.txt /home/
RUN pip install -r requirements.txt
COPY . /home/

RUN chown -R $APP_USER:$APP_USER $APP_HOME
USER $APP_USER

CMD ["gunicorn", "shadowmere.wsgi:application", "--bind", "0.0.0.0:8001", "-k", "gevent", "-w", "6", "--capture-output"]
