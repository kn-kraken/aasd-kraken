import inspect
import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import json
import threading
from dataclasses import dataclass
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))
from system_data import DEFAULT_METADATA

@dataclass
class TenantOfferDetails:
    min_price: float
    max_price: float
    location: tuple[float]


class FutureTenantAgent(Agent):
    def __init__(self, jid, password, event_queue, *args, **kwargs):
        super().__init__(jid, password, *args, **kwargs)
        self.event_queue = event_queue

    class RegisterRental(OneShotBehaviour):
        def __init__(self, tenant_offer_details: TenantOfferDetails):
            super().__init__()
            self.tenant_offer_details = tenant_offer_details

        async def run(self):
            print("RegisterRental running")
            msg = Message(
                to="hub_agent@localhost",
                metadata={
                    "performative": "inform",
                    "conversation-id": "register-rental",
                    **DEFAULT_METADATA,
                },
                body=json.dumps(
                    {
                        "min_price": self.tenant_offer_details.min_price,
                        "max_price": self.tenant_offer_details.max_price,
                        "location": self.tenant_offer_details.location,
                    }
                ),
            )
            await self.send(msg)

    class AuctionStart(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionStart got msg")

            data = json.loads(msg.body)
            offer_id = data["offer_id"]
            current_highest_bid = data["current_highest_bid"]

            self.agent.event_queue.put({"type": "auction-start", "data": {offer_id, current_highest_bid}, "agent": self.agent.jid})


        metadata = {"conversation-id": "auction-start"}

    class Bid(OneShotBehaviour):
        def __init__(self, offer_id, amount):
            super().__init__()
            self.offer_id = offer_id
            self.amount = amount

        async def run(self):
            await self.send(
                    Message(
                        to="hub_agent@localhost",
                        metadata={
                            "performative": "inform",
                            "conversation-id": "bid",
                            **DEFAULT_METADATA,
                        },
                        body=json.dumps({"data": {"offer_id": self.offer_id}, "amount": self.amount}),
                    )
            )


    class OutbidNotification(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("OutbidNotification got msg")
            data = json.loads(msg.body)

            current_highest_bid = data["current_highest_bid"]

            self.agent.event_queue.put({"type": "outbid-notification", "data": {current_highest_bid}, "agent": self.agent.jid})

        metadata = {"conversation-id": "outbid-notification"}

    class AuctionStop(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionStop got msg")

            # TODO: show popup on frontend
            self.agent.event_queue.put({"type": "auction-stop", "agent": self.agent.jid})

        metadata = {
            "conversation-id": "auction-stop",
            **DEFAULT_METADATA,
        }

    class ConfirmationRequest(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("ConfirmationRequest got msg")

            data = json.loads(msg.body)
            offer_id = data["offer_id"]
            bid_amount = data["bid_amount"]

            self.agent.event_queue.put({"type": "confirmation-request", "data": {offer_id, bid_amount}, "agent": self.agent.jid})

            # TODO: show popup on frontend


        metadata = {
            "conversation-id": "confirmation-request",
            **DEFAULT_METADATA,
        }

    class Confirm(OneShotBehaviour):
        def __init__(self, offer_id, confirmation):
            super().__init__()
            self.offer_id = offer_id
            self.confirmation = confirmation

        async def run(self):
            await self.send(
                Message(
                    to="hub_agent@localhost",
                    metadata={
                        "performative": "inform",
                        "conversation-id": "confirmation-response",
                        **DEFAULT_METADATA,
                    },
                    body=json.dumps(
                        {"offer_id": self.offer_id, "confirmed": self.confirmation}
                    ),
                )
            )

    class AuctionLost(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionLost got msg")

            self.agent.event_queue.put({"type": "auction-lost", "agent": self.agent.jid})

        metadata = {
            "conversation-id": "auction-lost",
            **DEFAULT_METADATA,
        }

    async def setup(self):
        for d in [
            d
            for d in dir(self)
            if inspect.isclass(getattr(self, d)) and d != "__class__"
        ]:
            attr = getattr(self, d)
            if issubclass(attr, CyclicBehaviour) and hasattr(attr, "metadata"):
                template = Template(metadata=attr.metadata)
                self.add_behaviour(attr(), template)

    def add_register_rental(self, tenant_offer_details: TenantOfferDetails):
        behavior = self.RegisterRental(tenant_offer_details)
        self.add_behaviour(behavior)

    def add_confirm(self, offer_id, confirmation):
        behavior = self.Confirm(offer_id, confirmation)
        self.add_behaviour(behavior)

    def add_bid(self, offer_id):
        behavior = self.Bid(offer_id)
        self.add_behaviour(behavior)


class FutureTenantInterface:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.agents = []

    def register_tenant(self, agent_id, tenant_offer_details: TenantOfferDetails):
        new_jid = f"{agent_id}@localhost"
        new_password = "some_password"
        new_agent = FutureTenantAgent(new_jid, new_password, self.event_queue)
        new_loop = asyncio.new_event_loop()

        def agent_thread_main():
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(new_agent.start(auto_register=True))
            new_loop.run_until_complete(spade.wait_until_finished(new_agent))

        t = threading.Thread(target=agent_thread_main, daemon=True)
        t.start()

        new_loop.call_soon_threadsafe(lambda: new_agent.add_register_rental(tenant_offer_details))

        self.agents.append({
            "agent": new_agent,
            "loop": new_loop,
            "thread": t,
            "jid": new_jid,
        })

    def add_bid_bhv(self, agent_id, offer_id, amount):
        agent_entry = next(
            (agent for agent in self.agents if agent["jid"] == agent_id), None
        )
        if not agent_entry:
            print("run bid: Agent not found")
            return

        agent = agent_entry["agent"]
        loop: asyncio.AbstractEventLoop = agent_entry["loop"]

        loop.call_soon_threadsafe(lambda: agent.add_bid(offer_id, amount))

    def add_confirm_bhv(self, agent_id, offer_id, confirmation):
        agent_entry = next(
            (agent for agent in self.agents if agent["jid"] == agent_id), None
        )
        if not agent_entry:
            print("run confirm: Agent not found")
            return

        agent = agent_entry["agent"]
        loop: asyncio.AbstractEventLoop = agent_entry["loop"]

        loop.call_soon_threadsafe(lambda: agent.add_confirm(offer_id, confirmation))

    def stop_all_agents(self):
        for agent_entry in self.agents:
            agent = agent_entry["agent"]
            loop = agent_entry["loop"]

            def stop_agent():
                loop.create_task(agent.stop())

            loop.call_soon_threadsafe(stop_agent)
        self.agents = []

async def main():
    future_tenant = FutureTenantAgent(
        "future_tenant@localhost", "future_tenant_password"
    )
    await future_tenant.start(auto_register=True)

    await spade.wait_until_finished(future_tenant)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
