# Shadowmere
An automatically tested list of Shadowsocks proxies.

## Motivation
Collecting proxies around the internet is fun, but what if they stop working? Just register them in your shadowmere and let it do the checking for you.

## How to install
### Dependencies
 - [Docker](https://www.docker.com/)
 - [docker-compose](https://docs.docker.com/compose/)
 - [minio](https://min.io/)
### Run
 1. Edit the `.env` file and set your desired secrets
 2. Run `docker-compose up -d --build`
 3. The website should be accessible in http://127.0.0.1:8001 and administration in http://127.0.0.1:8001/admin 
