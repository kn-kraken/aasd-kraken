from pathlib import Path
from testcontainers.core.container import DockerContainer
import asyncio
import pytest
import time
from spade.agent import Agent

from agents.hub.main import HubAgent
from agents.premise_for_rent.main import PremiseForRentAgent
from agents.future_tenant.main import FutureTenantAgent


def get_hub_agent():
    return HubAgent("hub_agent@localhost", "hub_agent_password")


def get_premise_for_rent_agent():
    return PremiseForRentAgent(
        "premise_for_rent_agent@localhost", "premise_for_rent_agent_password"
    )


def get_future_tenant_agent():
    return FutureTenantAgent("future_tenant@localhost", "future_tenant_password")


async def start_and_wait(agent: Agent, delay: int = 3):
    await agent.start(auto_register=True)
    await asyncio.sleep(delay)


@pytest.fixture(scope="session")
def xmpp_server():
    with DockerContainer("tigase/tigase-xmpp-server:8.0.0") as container:
        container.with_env("DB_ROOT_USER", "admin")
        container.with_env("DB_ROOT_PASS", "admin")
        container.with_env("ADMIN_JID", "admin@localhost")
        container.with_env("ADMIN_PASSWORD", "admin")
        container.with_volume_mapping(
            host=str(Path(__file__).parent / "tigase/config/tigase.conf"),
            container="/home/tigase/tigase-server/etc/tigase.conf",
        )
        container.with_volume_mapping(
            host=str(Path(__file__).parent / "tigase/config/config.tdsl"),
            container="/home/tigase/tigase-server/etc/config.tdsl",
        )
        container.with_bind_ports(
            container=5222,
            host=5222,
        )
        container.start()
        print("XMPP warmup")
        time.sleep(18)
        print("XMPP started")

        yield
