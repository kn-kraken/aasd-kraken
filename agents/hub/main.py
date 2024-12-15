import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template


class HubAgent(Agent):
    class RecvBehav(CyclicBehaviour):
        async def run(self):
            print("RecvBehav running")

            msg = await self.receive(timeout=20)
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")


    async def setup(self):
        print("HubAgent started")
        b = self.RecvBehav()
        template_inform = Template(metadata={"performative": "inform"})
        template_propose = Template(metadata={"performative": "propose"})
        template_request = Template(metadata={"performative": "request"})
        template_cancel = Template(metadata={"performative": "cancel"})
        template = (
            template_inform | template_propose | template_request | template_cancel
        )
        self.add_behaviour(b, template)


async def main():
    hub_agent = HubAgent("hub_agent@localhost", "hub_agent_password")
    await hub_agent.start(auto_register=True)
    print("hub_agent started")

    await spade.wait_until_finished(hub_agent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
