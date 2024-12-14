import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message


class PremiseForRentAgent(Agent):
    class OpenOfferRequest(OneShotBehaviour):
        async def run(self):
            print("OpenOfferRequest running")
            msg = Message(to="hub_agent@localhost")
            msg.set_metadata("performative", "propose")
            msg.body = "OpenOfferRequest details"
            await self.send(msg)
            await self.agent.stop()

    async def setup(self):
        print("PremiseForRentAgent started")
        self.add_behaviour(self.OpenOfferRequest())


async def main():
    premise_for_rent_agent = PremiseForRentAgent(
        "premise_for_rent_agent@localhost", "premise_for_rent_agent_password"
    )
    await premise_for_rent_agent.start(auto_register=True)

    await spade.wait_until_finished(premise_for_rent_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
