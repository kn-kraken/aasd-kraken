import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json


# AGENT
class CitizenAgent(Agent):
    class ServiceDemandRequest(OneShotBehaviour):
        def __init__(self, localization, service_type, priority):
            super().__init__()
            self.localization = localization
            self.service_type = service_type
            self.priority = priority


        async def run(self):
            print("ServiceDemandRequest running")
            msg = Message(
                to="hub_agent@localhost",
                metadata={
                    "performative": "inform",
                    "conversation_id": "ServiceDemandRequest",
                },
                body=json.dumps({
                    "localization": self.localization,
                    "service_type": self.service_type,
                    "priority": self.priority,
                }),
            )

            await self.send(msg)
            print("Message sent!")
            await self.agent.stop()

    def add_service_demand_request(self, localization, service_type, priority):
        behavior = self.ServiceDemandRequest(localization, service_type, priority)
        self.add_behaviour(behavior)


# API

async def main(localization, service_type, priority):
    agent = CitizenAgent("citizen_agent@localhost", "citizen_agent_password")
    await agent.start(auto_register=True)
    agent.add_service_demand_request(localization, service_type, priority)
    await spade.wait_until_finished(agent)
    await agent.stop()


def run_citizen_agent(localization, service_type, priority):
    spade.run(main(localization, service_type, priority))


if __name__ == "__main__":
    spade.run(main([1.0, 10.2], "Żabka", "High"))
