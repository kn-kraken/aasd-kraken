import asyncio
from datetime import timedelta
import pytest
from testing_common import (
    confirmation,
    get_from_queue,
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
    await rental_request_register(future_tenant, delay=0)
    event = await get_from_queue(future_tenant)

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
    await rental_request_register(future_tenant2, delay=0)
    _ = await get_from_queue(future_tenant)

    # when
    await add_bid(future_tenant, amount=120)
    await add_bid(future_tenant2, amount=140, delay=0)
    event = await asyncio.wait_for(future_tenant.event_queue.get(), timeout=10)

    # then
    assert (
        event["type"] == "outbid-notification"
    ), "Expected outbid-notification notification"


@pytest.mark.asyncio
async def test_auction_stop(xmpp):
    # given
    hub_agent = get_hub_agent(
        xmpp,
        auction_time=timedelta(seconds=5),
        extend_duration=timedelta(seconds=1),
    )
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)
    future_tenant = get_future_tenant_agent(xmpp)
    await rental_offer_register(hub_agent, premise_for_rent_agent)
    await rental_request_register(future_tenant)
    _ = await get_from_queue(future_tenant)

    # when
    await add_bid(future_tenant, amount=120, delay=0)
    event = await get_from_queue(future_tenant)

    # then
    assert event["type"] == "auction-stop", "Expected auction-stop notification"


@pytest.mark.asyncio
async def test_auction_confirmation_request(xmpp):
    # given
    hub_agent = get_hub_agent(
        xmpp,
        auction_time=timedelta(seconds=5),
        extend_duration=timedelta(seconds=1),
    )
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)
    future_tenant = get_future_tenant_agent(xmpp)
    await rental_offer_register(hub_agent, premise_for_rent_agent)
    await rental_request_register(future_tenant)
    _ = await get_from_queue(future_tenant)

    # when
    await add_bid(future_tenant, amount=120, delay=0)
    _ = await get_from_queue(future_tenant)
    event = await get_from_queue(future_tenant)

    # then
    assert (
        event["type"] == "confirmation-request"
    ), "Expected confirmation-request notification"


@pytest.mark.asyncio
async def test_auction_completed(xmpp):
    # given
    hub_agent = get_hub_agent(
        xmpp,
        auction_time=timedelta(seconds=5),
        extend_duration=timedelta(seconds=1),
    )
    premise_for_rent_agent = get_premise_for_rent_agent(xmpp)
    future_tenant = get_future_tenant_agent(xmpp)
    await rental_offer_register(hub_agent, premise_for_rent_agent)
    await rental_request_register(future_tenant)
    _ = await get_from_queue(future_tenant)
    await add_bid(future_tenant, amount=120, delay=0)
    _ = await get_from_queue(future_tenant)
    _ = await get_from_queue(future_tenant)

    # when
    await confirmation(future_tenant, delay=1)
    event = await get_from_queue(premise_for_rent_agent)

    # then
    assert (
        event["type"] == "auction-completed"
    ), "Expected auction-completed notification"
