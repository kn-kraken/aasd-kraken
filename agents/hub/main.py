import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template


class HubAgent(Agent):
    class RecvBehav(OneShotBehaviour):
        async def run(self):
            print("RecvBehav running")

            msg = await self.receive(timeout=20)
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

            await self.agent.stop()

    async def setup(self):
        print("HubAgent started")
        b = self.RecvBehav()
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(b, template)


async def main():
    hub_agent = HubAgent("hub_agent@server_hello", "hub_agent_password")
    await hub_agent.start(auto_register=True)
    print("hub_agent started")

    await spade.wait_until_finished(hub_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
