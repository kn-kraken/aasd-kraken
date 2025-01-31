import asyncio
import pytest
from testing_common import (
    get_hub_agent,
    add_bid,
    get_premise_for_rent_agent,
    get_future_tenant_agent,
    get_future_tenant_agent2,
    rental_offer_register,
    rental_request_register,
)
from testing_common import xmpp as xmpp


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
    future_tenant = get_future_tenant_agent(xmpp)
    await rental_offer_register(hub_agent, premise_for_rent_agent)

    # when
    await rental_request_register(future_tenant, delay=2)
    event = future_tenant.event_queue.get_nowait()

    # then
    assert event["type"] == "auction-start", "Expected auction-start notification"


@pytest.mark.asyncio
async def test_bid(xmpp):
    # given
    hub_agent = get_hub_agent(xmpp)
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)
    future_tenant = get_future_tenant_agent(xmpp)
    await rental_offer_register(hub_agent, premise_for_rent_agent)
    await rental_request_register(future_tenant)

    # when
    await add_bid(future_tenant, amount=120)

    # then
    assert len(hub_agent.active_auctions["0"].bids) == 1, "Hub should register a bid"


@pytest.mark.asyncio
async def test_outbid_notification(xmpp):
    # given
    hub_agent = get_hub_agent(xmpp)
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)
    future_tenant = get_future_tenant_agent(xmpp)
    future_tenant2 = get_future_tenant_agent2(xmpp)
    await rental_offer_register(hub_agent, premise_for_rent_agent)
    await rental_request_register(future_tenant)
    await rental_request_register(future_tenant2)
    _ = future_tenant.event_queue.get_nowait()

    # when
    await add_bid(future_tenant, amount=120)
    await add_bid(future_tenant2, amount=140, delay=2)
    event = future_tenant.event_queue.get_nowait()

    # then
    assert (
        event["type"] == "outbid-notification"
    ), "Expected outbid-notification notification"
