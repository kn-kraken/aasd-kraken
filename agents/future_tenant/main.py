import inspect
import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.template import Template
from spade.message import Message
import json


class FutureTenantAgent(Agent):
    class RegisterRental(OneShotBehaviour):
        async def run(self):
            print("RegisterRental running")
            msg = Message(
                to="hub_agent@localhost",
                metadata={
                    "performative": "inform",
                    "conversation-id": "register-rental",
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

            # TODO: show popup on frontend

        metadata = {
           "conversation-id": "auction-start"
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
