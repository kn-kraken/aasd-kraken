import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json

DEFAULT_METADATA = {
    "language": "JSON",
    "ontology": "kraken",
}


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

    def add_service_demand_request(self, localization, service_type, priority):
        behavior = self.ServiceDemandRequest(localization, service_type, priority)
        self.add_behaviour(behavior)


async def main():
    agent = CitizenAgent("citizen_agent@localhost", "citizen_agent_password")
    await agent.start(auto_register=True)
    agent.add_service_demand_request([1.0, 10.2], "Żabka", "High")

    await spade.wait_until_finished(agent)

    await agent.stop()


if __name__ == "__main__":
    spade.run(main())
