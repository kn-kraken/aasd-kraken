import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
import json


class HubAgent(Agent):
    class OpenOfferRequestRecvBehav(CyclicBehaviour):
        async def run(self):
            print("OpenOfferRequestRecvBehav running")
            msg = await self.receive(timeout=20)
            if msg:
                print("Message received with content: {}".format(msg.body))
                offer = json.loads(msg.body)
                print(offer["price"])
            else:
                print("Did not received any message after 10 seconds")

    class ServiceDemandRequestRecvBehav(CyclicBehaviour):
        async def run(self):
            print("OpenOfferRequestRecvBehav running")
            msg = await self.receive(timeout=20)
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

    class StartNegotiationRecvBehav(CyclicBehaviour):
        async def run(self):
            print("StartNegotiationRecvBehav running")
            msg = await self.receive(timeout=20)
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

    async def setup(self):
        print("HubAgent started")
        self.add_behaviour(
            self.OpenOfferRequestRecvBehav(),
            Template(
                metadata={
                    "performative": "propose",
                    "conversation_id ": "OpenOfferRequest",
                }
            ),
        )
        self.add_behaviour(
            self.ServiceDemandRequestRecvBehav(),
            Template(
                metadata={
                    "performative": "inform",
                    "conversation_id ": "ServiceDemandRequest",
                }
            ),
        )
        self.add_behaviour(
            self.ServiceDemandRequestRecvBehav(),
            Template(
                metadata={
                    "performative": "propose",
                    "conversation_id ": "StartNegotiation",
                }
            ),
        )


async def main():
    hub_agent = HubAgent("hub_agent@localhost", "hub_agent_password")
    await hub_agent.start(auto_register=True)
    print("hub_agent started")

    await spade.wait_until_finished(hub_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
