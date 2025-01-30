import asyncio
import pytest
from testing_common import xmpp as xmpp
from testing_common import (
    get_hub_agent,
    get_premise_for_rent_agent,
    get_future_tenant_agent,
    rental_offer_register,
    rental_request_register,
)


@pytest.mark.asyncio
async def test_rental_offer_register(xmpp):
    # given
    hub_agent = get_hub_agent(xmpp)
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)

    # when
    await rental_offer_register(hub_agent, premise_for_rent_agent)

    # then
    assert (
        len(hub_agent.rental_offers) == 1
    ), "Premise for rent should register 1 rental offer in Hub"


@pytest.mark.asyncio
async def test_rental_request_register(xmpp):
    # given
    hub_agent = get_hub_agent(xmpp)
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)
    future_tenant = get_future_tenant_agent(xmpp)
    await rental_offer_register(hub_agent, premise_for_rent_agent)

    # when
    await rental_request_register(future_tenant)

    # then
    assert (
        len(hub_agent.rental_requests) == 1
    ), "Future tenant should register 1 rental offer in Hub"


@pytest.mark.asyncio
async def test_auction_start(xmpp):
    # given
    hub_agent = get_hub_agent(xmpp)
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)
    event_queue = asyncio.Queue()
    future_tenant = get_future_tenant_agent(xmpp, event_queue)
    await rental_offer_register(hub_agent, premise_for_rent_agent)

    # when
    await rental_request_register(future_tenant, delay=0)
    event = await event_queue.get()

    # then
    assert event["type"] == "auction-start", "Expected auction-start notification"
