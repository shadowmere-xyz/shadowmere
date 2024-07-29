# Shadowmere
An automatically tested list of Shadowsocks proxies.

## Motivation
Collecting proxies around the internet is fun, but what if they stop working? Just register them in your shadowmere and let it do the checking for you.

## See it in action
I have started an instance at [https://shadowmere.xyz/](https://shadowmere.xyz/). Feel free to go click around.
If you want the simpler but uglier interface you can check it at https://old.shadowmere.akiel.dev/.
And if you are using Tor you can directly use the hidden service at http://eb7x5hfb3vbb3zgrzi6qf6sqwks64fp63a7ckdl3sdw5nb6bgvskvpyd.onion

## How to install
### Dependencies
 - [Docker](https://www.docker.com/)
 - [docker-compose](https://docs.docker.com/compose/)
 - [minio](https://min.io/)
### Run
 1. Edit the `.env` file and set your desired secrets
 2. Run `docker-compose up -d --build`
 3. The website should be accessible in http://127.0.0.1:8001 (old interface), http://127.0.0.1:8000 (new interface), and administration in http://127.0.0.1:8001/admin 
### Frontend
The new interface is powered by [https://github.com/swordfest/shadowmere-njs](https://github.com/shadowmere-xyz/shadowmere-njs)
