FROM python:3.9
WORKDIR /home/

COPY requirements.txt /home/
RUN pip install -r requirements.txt
RUN wget https://github.com/shadowsocks/shadowsocks-rust/releases/download/v1.11.2/shadowsocks-v1.11.2.x86_64-unknown-linux-gnu.tar.xz
RUN tar -xf shadowsocks-v1.11.2.x86_64-unknown-linux-gnu.tar.xz && mv ss* /usr/bin
COPY . /home/

CMD ["gunicorn", "shadowmere.asgi:application", "--bind", "0.0.0.0:8001", "-k", "uvicorn.workers.UvicornWorker"]
