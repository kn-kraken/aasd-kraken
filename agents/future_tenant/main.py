import inspect
import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import json
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))
from system_data import DEFAULT_METADATA

class FutureTenantAgent(Agent):
    class RegisterRental(OneShotBehaviour):
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
                        "min_price": 100,
                        "max_price": 200,
                        "location": [50.0, 100.0],  # TODO: lat/lon
                    }
                ),
            )
            await self.send(msg)
            # await self.agent.stop()

    class AuctionStart(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionStart got msg")

            data = json.loads(msg.body)
            offer_id = data["offer_id"]

            # TODO: show popup on frontend

            # TODO: below line is a simulation, this should be oneshot connected to frontend
            await asyncio.sleep(2)
            await self.send(
                Message(
                    to="hub_agent@localhost",
                    metadata={
                        "performative": "inform",
                        "conversation-id": "bid",
                        **DEFAULT_METADATA,
                    },
                    body=json.dumps({"offer_id": offer_id, "amount": 99990}),
                )
            )

        metadata = {"conversation-id": "auction-start"}

    class OutbidNotification(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("OutbidNotification got msg")

            # TODO: show popup on frontend

        metadata = {"conversation-id": "outbid-notification"}

    class AuctionStop(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionStop got msg")

            # TODO: show popup on frontend

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

            # TODO: show popup on frontend

            # TODO: below is a simulation, connect this to FE
            await asyncio.sleep(5)
            await self.send(
                Message(
                    to="hub_agent@localhost",
                    metadata={
                        "performative": "inform",
                        "conversation-id": "confirmation-response",
                        **DEFAULT_METADATA,
                    },
                    body=json.dumps(
                        {"offer_id": offer_id, "confirmed": True}  # TODO: set it in FE
                    ),
                )
            )

        metadata = {
            "conversation-id": "confirmation-request",
            **DEFAULT_METADATA,
        }

    class AuctionLost(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if not msg:
                return
            print("AuctionLost got msg")

            # TODO: show popup on frontend

        metadata = {
            "conversation-id": "auction-lost",
            **DEFAULT_METADATA,
        }

    async def setup(self):
        print("FutureTenantAgent started")
        self.add_behaviour(self.RegisterRental())

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
    future_tenant = FutureTenantAgent(
        "future_tenant@localhost", "future_tenant_password"
    )
    await future_tenant.start(auto_register=True)

    await spade.wait_until_finished(future_tenant)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
