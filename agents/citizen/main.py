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
class CitizenAgent(Agent):
    class ServiceDemandRequest(OneShotBehaviour):
        def __init__(self, service_demand: ServiceDemand):
            super().__init__()
            self.service_demand = service_demand

        async def run(self):
            print("ServiceDemandRequest running")
            msg = Message(
                to="hub_agent@localhost",
                metadata={
                    "performative": "inform",
                    "conversation_id": "ServiceDemandRequest",
                },
                body=json.dumps({
                    "localization": self.service_demand.localization,
                    "service_type": self.service_demand.service_type,
                    "priority": self.service_demand.priority,
                }),
            )

            await self.send(msg)
            print("Message sent!")
            await self.agent.stop()

    def add_service_demand_request(self, service_demand: ServiceDemand):
        behavior = self.ServiceDemandRequest(service_demand)
        self.add_behaviour(behavior)

# API
async def main(service_demand: ServiceDemand):
    agent = CitizenAgent("citizen_agent@localhost", "citizen_agent_password")
    await agent.start(auto_register=True)
    agent.add_service_demand_request(service_demand)
    await spade.wait_until_finished(agent)
    await agent.stop()

def run_citizen_agent(service_demand: ServiceDemand):
    spade.run(main(service_demand))

if __name__ == "__main__":
    service_demand = ServiceDemand(localization=[1.0, 10.2], service_type="Żabka", priority="High")
    spade.run(main(service_demand))