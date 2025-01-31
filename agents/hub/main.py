import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
import json
import inspect
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import uuid
import sys
import os


sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
)
from system_data import DEFAULT_METADATA


@dataclass
class RentalOffer:
    agent_jid: str
    starting_price: int
    location: tuple[float, float]


@dataclass
class RentalRequest:
    min_price: int
    max_price: int
    location: tuple[float, float]
    agent_jid: str


def is_close(location1, location2):
    return (
        abs(location1[0] - location2[0]) < 0.01
        and abs(location1[1] - location2[1]) < 0.01
    )


@dataclass
class Bid:
    bidder_jid: str
    amount: int
    timestamp: datetime


@dataclass
class Auction:
    offer: RentalOffer
    bids: List[Bid]
    end_time: datetime
    status: str  # 'bidding', 'confirming', 'completed'
    current_confirming_bidder: Optional[str] = None
    confirmation_deadline: Optional[datetime] = None

    def extend_duration(self, duration: timedelta):
        new_end_time = datetime.now() + duration
        if new_end_time > self.end_time:
            self.end_time = new_end_time

    def get_outbid_agents(self, amount: int) -> List[str]:
        return [bid.bidder_jid for bid in self.bids if bid.amount < amount]

    def get_winning_bids(self) -> List[Bid]:
        return sorted(self.bids, key=lambda x: (-x.amount, x.timestamp))


class HubAgent(Agent):
    def __init__(
        self,
        jid,
        password,
        auction_time=timedelta(seconds=20),
        extend_duration=timedelta(seconds=5),
    ):
        super().__init__(jid, password)
        self.rental_offers = []
        self.rental_requests = []
        self.active_auctions: Dict[str, Auction] = {}  # offer_id -> Auction
        self.auction_time = auction_time
        self.extend_duration = extend_duration

    class RegisterRentalRequestRecvBhv(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return

            data = json.loads(msg.body)
            request = RentalRequest(
                min_price=data["min_price"],
                max_price=data["max_price"],
                location=tuple(data["location"]),
                agent_jid=str(msg.sender),
            )

            # Store the request
            self.agent.rental_requests.append(request)

            # Check for matching offers that already have active auctions
            for offer_id, auction in self.agent.active_auctions.items():
                if (
                    is_close(auction.offer.location, request.location)
                    and request.min_price
                    <= auction.offer.starting_price
                    <= request.max_price
                ):
                    auction.bids.append(
                        Bid(
                            bidder_jid=request.agent_jid,
                            amount=auction.offer.starting_price,
                            timestamp=datetime.now(),
                        )
                    )
                    # Notify the requester about the existing auction
                    msg = spade.message.Message(
                        to=request.agent_jid,
                        metadata={"conversation-id": "auction-start"},
                        body=json.dumps(
                            {
                                "offer_id": offer_id,
                                "starting_price": auction.offer.starting_price,
                                "location": auction.offer.location,
                                "current_highest_bid": max(
                                    (bid.amount for bid in auction.bids),
                                    default=auction.offer.starting_price,
                                ),
                                "end_time": auction.end_time.isoformat(),
                            }
                        ),
                    )
                    await self.send(msg)

            # Check for matching offers that don't have auctions yet
            matching_offers = [
                (offer_id, offer)
                for offer_id, offer in enumerate(self.agent.rental_offers)
                if (
                    is_close(offer.location, request.location)
                    and request.min_price <= offer.starting_price <= request.max_price
                    and str(offer_id) not in self.agent.active_auctions
                )
            ]

            # Start new auctions if there are multiple requests for the same offer
            for offer_id, offer in matching_offers:
                matching_requests = [
                    req
                    for req in self.agent.rental_requests
                    if (
                        is_close(offer.location, req.location)
                        and req.min_price <= offer.starting_price <= req.max_price
                    )
                ]

                if (
                    len(matching_requests) >= 1
                    and str(offer_id) not in self.agent.active_auctions
                ):
                    # Create new auction
                    auction = Auction(
                        offer=offer,
                        bids=[],
                        end_time=datetime.now() + self.agent.auction_time,
                        status="bidding",
                    )
                    self.agent.active_auctions[str(offer_id)] = auction

                    # Notify all matching requesters about the new auction
                    for req in matching_requests:
                        auction.bids.append(
                            Bid(
                                bidder_jid=req.agent_jid,
                                amount=offer.starting_price,
                                timestamp=datetime.now(),
                            )
                        )
                        msg = spade.message.Message(
                            to=req.agent_jid,
                            metadata={"conversation-id": "auction-start"},
                            body=json.dumps(
                                {
                                    "offer_id": str(offer_id),
                                    "starting_price": offer.starting_price,
                                    "location": offer.location,
                                    "end_time": auction.end_time.isoformat(),
                                }
                            ),
                        )
                        await self.send(msg)
                    print("New auction started")

        metadata = {
            "performative": "inform",
            "conversation-id": "register-rental",
            **DEFAULT_METADATA,
        }

    class RegisterRentalOfferRecvBhv(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("RegisterRentalOfferRecvBhv got msg")

            data = json.loads(msg.body)
            offer = RentalOffer(**data, agent_jid=str(msg.sender))
            offer_id = str(uuid.uuid4())

            matching_requests = [
                request
                for request in self.agent.rental_requests
                if is_close(offer.location, request.location)
                and request.min_price <= offer.starting_price <= request.max_price
            ]

            if len(matching_requests) >= 1:
                auction = Auction(
                    offer=offer,
                    bids=[],
                    end_time=datetime.now() + self.agent.auction_time,
                    status="bidding",
                )
                self.agent.active_auctions[offer_id] = auction

                # Notify all matching requesters about the auction
                for request in matching_requests:
                    auction.bids.append(
                        Bid(
                            bidder_jid=request.agent_jid,
                            amount=offer.starting_price,
                            timestamp=datetime.now(),
                        )
                    )
                    msg = spade.message.Message(
                        to=request.agent_jid,
                        metadata={
                            "conversation-id": "auction-start",
                            **DEFAULT_METADATA,
                        },
                        body=json.dumps(
                            {
                                "offer_id": offer_id,
                                "starting_price": offer.starting_price,
                                "location": offer.location,
                                "end_time": auction.end_time.isoformat(),
                            }
                        ),
                    )
                    await self.send(msg)

            self.agent.rental_offers.append(offer)

        metadata = {
            "performative": "inform",
            "conversation-id": "rental-offer",
        }

    class HandleBidBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return

            data = json.loads(msg.body)
            offer_id = data["offer_id"]
            bid_amount = data["amount"]
            bidder_jid = str(msg.sender)

            auction = self.agent.active_auctions.get(offer_id)
            if not auction or auction.status != "bidding":
                return

            # Record the bid
            new_bid = Bid(
                bidder_jid=bidder_jid, amount=bid_amount, timestamp=datetime.now()
            )
            current_bid = next(
                (
                    i
                    for i, bid in enumerate(auction.bids)
                    if bid.bidder_jid == bidder_jid
                ),
            )
            if new_bid.amount <= auction.bids[current_bid].amount:
                return

            auction.bids[current_bid] = new_bid
            auction.extend_duration(self.agent.extend_duration)

            # Notify outbid agents
            outbid_agents = auction.get_outbid_agents(bid_amount)
            for agent_jid in outbid_agents:
                msg = spade.message.Message(
                    to=agent_jid,
                    metadata={"conversation-id": "outbid-notification"},
                    body=json.dumps(
                        {"offer_id": offer_id, "current_highest_bid": bid_amount}
                    ),
                )
                await self.send(msg)

        metadata = {
            "performative": "inform",
            "conversation-id": "bid",
        }

    class AuctionManagerBehaviour(CyclicBehaviour):
        async def run(self):
            await asyncio.sleep(1)  # Check every second
            now = datetime.now()

            for offer_id, auction in list(self.agent.active_auctions.items()):
                if auction.status == "bidding" and now >= auction.end_time:
                    # Transition to confirmation phase
                    auction.status = "confirming"

                    # Notify all bidders
                    for bid in auction.bids:
                        msg = spade.message.Message(
                            to=bid.bidder_jid,
                            metadata={
                                "conversation-id": "auction-stop",
                                **DEFAULT_METADATA,
                            },
                            body=json.dumps(
                                {
                                    "offer_id": offer_id,
                                }
                            ),
                        )
                        await self.send(msg)

                    winning_bids = auction.get_winning_bids()
                    if winning_bids:
                        auction.current_confirming_bidder = winning_bids[0].bidder_jid
                        auction.confirmation_deadline = now + timedelta(seconds=20)

                        # Ask for confirmation
                        msg = spade.message.Message(
                            to=auction.current_confirming_bidder,
                            metadata={
                                "conversation-id": "confirmation-request",
                                **DEFAULT_METADATA,
                            },
                            body=json.dumps(
                                {
                                    "offer_id": offer_id,
                                    "bid_amount": winning_bids[0].amount,
                                }
                            ),
                        )
                        await self.send(msg)

                elif (
                    auction.status == "confirming"
                    and now >= auction.confirmation_deadline
                ):
                    # Move to next bidder or close auction
                    winning_bids = auction.get_winning_bids()
                    current_index = next(
                        (
                            i
                            for i, bid in enumerate(winning_bids)
                            if bid.bidder_jid == auction.current_confirming_bidder
                        ),
                        -1,
                    )

                    if current_index + 1 < len(winning_bids):
                        # Try next bidder
                        auction.current_confirming_bidder = winning_bids[
                            current_index + 1
                        ].bidder_jid
                        auction.confirmation_deadline = now + timedelta(seconds=20)

                        msg = spade.message.Message(
                            to=auction.current_confirming_bidder,
                            metadata={
                                "conversation-id": "confirmation-request",
                                **DEFAULT_METADATA,
                            },
                            body=json.dumps(
                                {
                                    "offer_id": offer_id,
                                    "bid_amount": winning_bids[
                                        current_index + 1
                                    ].amount,
                                }
                            ),
                        )
                        await self.send(msg)
                    else:
                        # No more bidders, close auction
                        auction.status = "completed"
                        del self.agent.active_auctions[offer_id]

    class HandleConfirmationBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return

            data = json.loads(msg.body)
            offer_id = data["offer_id"]
            confirmed = data["confirmed"]
            bidder_jid = str(msg.sender)

            auction = self.agent.active_auctions.get(offer_id)
            if not auction or auction.status != "confirming":
                return

            if confirmed and bidder_jid == auction.current_confirming_bidder:
                winner_bid = next(
                    bid for bid in auction.bids if bid.bidder_jid == bidder_jid
                )

                winning_bids = auction.get_winning_bids()
                current_index = next(
                    (
                        i
                        for i, bid in enumerate(winning_bids)
                        if bid.bidder_jid == auction.current_confirming_bidder
                    ),
                    -1,
                )

                if current_index + 1 < len(winning_bids):
                    for losing_bid in winning_bids[current_index + 1 :]:
                        msg = spade.message.Message(
                            to=losing_bid.bidder_jid,
                            metadata={
                                "conversation-id": "auction-lost",
                                **DEFAULT_METADATA,
                            },
                            body=json.dumps({"offer_id": offer_id}),
                        )
                        await self.send(msg)

                # Notify seller
                msg = spade.message.Message(
                    to=auction.offer.agent_jid,
                    metadata={
                        "conversation-id": "auction-completed",
                        **DEFAULT_METADATA,
                    },
                    body=json.dumps(
                        {"offer_id": offer_id, "final_price": winner_bid.amount}
                    ),
                )
                await self.send(msg)

                auction.status = "completed"
                del self.agent.active_auctions[offer_id]

        metadata = {
            "performative": "inform",
            "conversation-id": "confirmation-response",
            **DEFAULT_METADATA,
        }

    async def setup(self):
        print("HubAgent started")

        self.add_behaviour(self.AuctionManagerBehaviour())

        for d in [
            d
            for d in dir(self)
            if inspect.isclass(getattr(self, d)) and d != "__class__"
        ]:
            attr = getattr(self, d)
            if issubclass(attr, CyclicBehaviour) and hasattr(attr, "metadata"):
                template = Template(metadata=attr.metadata)
                self.add_behaviour(attr(), template)


async def main():
    hub_agent = HubAgent("hub_agent@localhost", "hub_agent_password")
    await hub_agent.start(auto_register=True)
    hub_agent.web.start(hostname="127.0.0.1", port=10001)
    print("hub_agent started")

    await spade.wait_until_finished(hub_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
