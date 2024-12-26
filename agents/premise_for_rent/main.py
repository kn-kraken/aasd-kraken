import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json


class PremiseForRentAgent(Agent):
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
            await self.agent.stop()

    async def setup(self):
        print("PremiseForRentAgent started")
        self.add_behaviour(self.RegisterRental())


async def main():
    premise_for_rent_agent = PremiseForRentAgent(
        "premise_for_rent_agent@localhost", "premise_for_rent_agent_password"
    )
    await premise_for_rent_agent.start(auto_register=True)

    await spade.wait_until_finished(premise_for_rent_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
