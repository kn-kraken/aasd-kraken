#!/bin/sh

docker compose build

# Start server
docker compose up server_hello -d
sleep 15

# Start agents
docker compose up agent_hub -d
sleep 2
docker compose up agent_citizen -d