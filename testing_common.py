from datetime import timedelta
from pathlib import Path
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import asyncio
import pytest
import time
from spade.agent import Agent

from agents.hub.main import HubAgent
from agents.premise_for_rent.main import PremiseForRentAgent, RentalOfferDetails
from agents.future_tenant.main import FutureTenantAgent, TenantOfferDetails


def get_hub_agent(
    xmpp_server,
    auction_time=timedelta(seconds=120),
    extend_duration=timedelta(seconds=60),
):
    return HubAgent(
        jid=f"hub_agent@{xmpp_server['ip']}",
        password="hub_agent_password",
        auction_time=auction_time,
        extend_duration=extend_duration,
    )


def get_premise_for_rent_agent(
    xmpp_server,
    event_queue=asyncio.Queue(),
) -> PremiseForRentAgent:
    return PremiseForRentAgent(
        f"premise_for_rent_agent@{xmpp_server['ip']}",
        "premise_for_rent_agent_password",
        event_queue,
    )


def get_future_tenant_agent(
    xmpp_server,
    event_queue=asyncio.Queue(),
) -> FutureTenantAgent:
    return FutureTenantAgent(
        f"future_tenant@{xmpp_server['ip']}",
        "future_tenant_password",
        event_queue,
    )


def get_future_tenant_agent2(
    xmpp_server,
    event_queue=asyncio.Queue(),
) -> FutureTenantAgent:
    return FutureTenantAgent(
        f"future_tenant2@{xmpp_server['ip']}",
        "future_tenant_password2",
        event_queue,
    )


def get_rental_offer_details() -> RentalOfferDetails:
    return RentalOfferDetails(
        starting_price=100.0,
        location=[52.2297700, 21.0117800],
    )


def get_tenant_offer_details() -> TenantOfferDetails:
    return TenantOfferDetails(
        min_price=50.0,
        max_price=200.0,
        location=[52.2297700, 21.0117800],
    )


async def get_from_queue(agent, timeout=10):
    event = await asyncio.wait_for(agent.event_queue.get(), timeout=timeout)
    return event


async def rental_offer_register(hub_agent, premise_for_rent_agent: PremiseForRentAgent):
    await start_and_wait(hub_agent)
    await start_and_wait(premise_for_rent_agent, delay=1)
    premise_for_rent_agent.add_service_demand_request(get_rental_offer_details())
    await wait(2)


async def rental_request_register(future_tenant: FutureTenantAgent, delay=2):
    await start_and_wait(future_tenant, 1)
    future_tenant.add_register_rental(get_tenant_offer_details())
    await wait(delay)


async def start_and_wait(agent: Agent, delay: int = 3):
    await agent.start(auto_register=True)
    await wait(delay)


async def add_bid(future_tenant: FutureTenantAgent, amount, delay=2):
    future_tenant.add_bid(
        offer_id="0",
        amount=amount,
    )
    await wait(delay)


async def confirmation(future_tenant: FutureTenantAgent, confirmation=True, delay=2):
    future_tenant.add_confirm(
        offer_id="0",
        confirmation=confirmation,
    )
    await wait(delay)


async def wait(delay: int):
    await asyncio.sleep(delay)


@pytest.fixture(scope="session")
def xmpp():
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
        # sadly spade does not support custom xmpp ports, so multiple instances of xmpp with dynamic ports cannot be used
        container.with_bind_ports(
            container=5222,
            host=5222,
        )
        container.start()
        print("XMPP warmup")
        wait_for_logs(container, "Server finished starting up", timeout=60)
        print("XMPP started")

        yield {
            "ip": container.get_container_host_ip(),
        }
