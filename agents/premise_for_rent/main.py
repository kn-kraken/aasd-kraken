from dataclasses import dataclass
import inspect
import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json
import sys
import threading
import asyncio
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))
from system_data import DEFAULT_METADATA

@dataclass
class RentalOfferDetails:
    starting_price: float
    location: list[float]


class PremiseForRentAgent(Agent):
    def __init__(self, jid, password, event_queue, *args, **kwargs):
        super().__init__(jid, password, *args, **kwargs)
        self.event_queue = event_queue

    class RentalOffer(OneShotBehaviour):
        def __init__(self, rental_offer_details: RentalOfferDetails):
            super().__init__()
            self.rental_offer_details = rental_offer_details

        async def run(self):
            print("RentalOffer running")
            msg = Message(
                to="hub_agent@localhost",
                metadata={
                    "performative": "inform",
                    "conversation-id": "rental-offer",
                    **DEFAULT_METADATA,
                },
                body=json.dumps(
                    {
                        "starting_price": self.rental_offer_details.starting_price,
                        "location": self.rental_offer_details.location,
                    }
                ),
            )
            await self.send(msg)

    class AuctionLost(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionLost got msg")


        metadata = {
            "conversation-id": "auction-lost",
            **DEFAULT_METADATA,
        }

    class AuctionCompleted(CyclicBehaviour):
        async def run(self):
            print("AuctionCompleted running")
            await self.agent.event_queue.put({"type": "auction-completed", "agent": self.agent.jid})
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionCompleted got msg")


            # TODO: show popup on frontend


        metadata = {
            "conversation-id": "auction-completed",
            **DEFAULT_METADATA,
        }


    async def setup(self):
        print("PremiseForRentAgent started")

        for d in [
            d
            for d in dir(self)
            if inspect.isclass(getattr(self, d)) and d != "__class__"
        ]:
            attr = getattr(self, d)
            if issubclass(attr, CyclicBehaviour) and hasattr(attr, "metadata"):
                template = Template(metadata=attr.metadata)
                self.add_behaviour(attr(), template)

    def add_service_demand_request(self, rental_offer_details: RentalOfferDetails):
        behavior = self.RentalOffer(rental_offer_details)
        self.add_behaviour(behavior)


class PremiseForRentAgentInterface:
    def __init__(self, name, event_queue):
        self.event_queue = event_queue
        self.loop = asyncio.new_event_loop()
        self.agent = PremiseForRentAgent(
            "premise_for_rent_agent@localhost",
            "premise_for_rent_agent_password",
            self.event_queue
        )
        self.thread = threading.Thread(target=self._thread_main, daemon=True)

    def start(self):
        self.thread.start()

    def _thread_main(self):
        asyncio.set_event_loop(self.loop)

        async def start_agent():
            await self.agent.start(auto_register=True)
            await spade.wait_until_finished(self.agent)

        self.loop.run_until_complete(start_agent())

    def add_rental_offer(self, rental_offer_details):
        self.loop.call_soon_threadsafe(lambda: self.agent.add_service_demand_request(rental_offer_details))



async def main():
    premise_for_rent_agent = PremiseForRentAgent(
        "premise_for_rent_agent@localhost", "premise_for_rent_agent_password"
    )
    await premise_for_rent_agent.start(auto_register=True)
    await spade.wait_until_finished(premise_for_rent_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
