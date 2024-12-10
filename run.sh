#!/bin/sh

docker compose up --build server_hello -d
sleep 1
docker compose up --build spade_hello -d