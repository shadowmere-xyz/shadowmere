FROM ghcr.io/shadowsocks/sslocal-rust:latest

USER root
RUN apk add curl
USER nobody

ADD sstest /usr/bin/

ENTRYPOINT [ "/usr/bin/sstest" ]
