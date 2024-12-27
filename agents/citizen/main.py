from dataclasses import dataclass
import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json

@dataclass
class ServiceDemand:
    localization: tuple[float, float]
    service_type: str
    priority: str

# AGENT
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))
from system_data import DEFAULT_METADATA


class CitizenAgent(Agent):
    class ServiceDemandRequest(OneShotBehaviour):
        def __init__(self, service_demand: ServiceDemand):
            super().__init__()
            self.service_demand = service_demand
            self.localization = service_demand.localization
            self.service_type = service_demand.service_type
            self.priority = service_demand.priority

        async def run(self):
            print("ServiceDemandRequest running")
            msg = Message(
                to="hub_agent@localhost",
                metadata={
                    "performative": "inform",
                    "conversation_id": "ServiceDemandRequest",
                    **DEFAULT_METADATA,
                },
                body=json.dumps(
                    {
                        "localization": self.localization,
                        "service_type": self.service_type,
                        "priority": self.priority,
                    }
                ),
            )

            await self.send(msg)
            print("Message sent!")
            await self.agent.stop()

    def add_service_demand_request(self, service_demand: ServiceDemand):
        behavior = self.ServiceDemandRequest(service_demand)
        self.add_behaviour(behavior)


async def main():
    agent = CitizenAgent("citizen_agent@localhost", "citizen_agent_password")
    await agent.start(auto_register=True)
    agent.add_service_demand_request(service_demand)
    await spade.wait_until_finished(agent)
    await agent.stop()


if __name__ == "__main__":
    service_demand = ServiceDemand(localization=[1.0, 10.2], service_type="Żabka", priority="High")
    spade.run(main(service_demand))