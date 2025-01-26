import pytest
from agents.hub.main import HubAgent
from agents.premise_for_rent.main import PremiseForRentAgent
from agents.future_tenant.main import FutureTenantAgent
from testing_common import (
    xmpp_server,
    start_and_wait,
    get_hub_agent,
    get_premise_for_rent_agent,
    get_future_tenant_agent,
)


@pytest.mark.asyncio
async def test_rental_offer_register(xmpp_server):
    hub_agent = get_hub_agent()
    premise_for_rent_agent = get_premise_for_rent_agent()

    try:
        await start_and_wait(hub_agent)
        await start_and_wait(premise_for_rent_agent)

        assert (
            len(hub_agent.rental_offers) == 1
        ), "Premise for rent should register 1 rental offer in Hub"
    finally:
        await hub_agent.stop()
        await premise_for_rent_agent.stop()


@pytest.mark.asyncio
async def test_rental_request_register(xmpp_server):
    hub_agent = get_hub_agent()
    premise_for_rent_agent = get_premise_for_rent_agent()
    future_tenant = get_future_tenant_agent()

    try:
        await start_and_wait(hub_agent)
        await start_and_wait(premise_for_rent_agent)
        await start_and_wait(future_tenant)

        assert (
            len(hub_agent.rental_offers) == 1
        ), "Premise for rent should register 1 rental offer in Hub"
        assert (
            len(hub_agent.rental_requests) == 1
        ), "Future tenant should register 1 rental offer in Hub"
    finally:
        await hub_agent.stop()
        await premise_for_rent_agent.stop()
