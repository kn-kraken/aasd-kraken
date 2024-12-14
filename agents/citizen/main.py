import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template


class CitizenAgent(Agent):
    class ServiceDemandRequest(OneShotBehaviour):
        async def run(self):
            print("ServiceDemandRequest running")
            msg = Message(to="hub_agent@server_hello")
            msg.set_metadata("performative", "inform")
            msg.body = "We need more żabkas in this area"

            await self.send(msg)
            print("Message sent!")

            await self.agent.stop()

    async def setup(self):
        print("CitizenAgent started")
        b = self.ServiceDemandRequest()
        self.add_behaviour(b)



async def main():
    citizen_agent = CitizenAgent("citizen_agent@server_hello", "citizen_agent_password")
    await citizen_agent.start(auto_register=True)
    print("citizen_agent started")

    await spade.wait_until_finished(citizen_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())