import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
import json
from dataclasses import dataclass


@dataclass
class RentalOffer:
    price: int
    location: tuple[float, float]


@dataclass
class RentalRequest:
    price: int


class HubAgent(Agent):
    def __init__(self):
        self.rental_offers = []
        self.rental_requests = []

    class ServiceDemandRequestRecvBhv(CyclicBehaviour):
        def __init__(self, hub):
            self.hub = hub

        async def run(self):
            print("OpenOfferRequestRecvBhv running")
            msg = await self.receive(timeout=20)
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

        metadata = {
            "performative": "inform",
            "conversation_id ": "ServiceDemandRequest",
        }

    class RegisterRentalOfferRecvBhv(CyclicBehaviour):
        def __init__(self, hub):
            self.hub = hub

        async def run(self):
            msg = await self.receive(timeout=20)
            data = json.loads(msg.body)
            self.rental_offers.append(RentalOffer(**data))

        metadata = {
            "performative": "inform",
            "conversation_id ": "RegisterRentalOffer",
        }

    class RegisterRentalRequestRecvBhv(CyclicBehaviour):
        def __init__(self, hub):
            self.hub = hub

        async def run(self):
            msg = await self.receive(timeout=20)
            data = json.loads(msg.body)
            self.rental_requests.append(RentalRequest(**data))

        metadata = {
            "performative": "inform",
            "conversation_id ": "RegisterRentalRequest",
        }

    async def setup(self):
        print("HubAgent started")

        for attr in self.__dict__.values():
            if (
                isinstance(attr, CyclicBehaviour)
                and (metadata := getattr(attr, "metadata", None)) is not None
            ):
                self.add_behaviour(attr(self), Template(metadata=metadata))


async def main():
    hub_agent = HubAgent("hub_agent@localhost", "hub_agent_password")
    await hub_agent.start(auto_register=True)
    print("hub_agent started")

    await spade.wait_until_finished(hub_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
