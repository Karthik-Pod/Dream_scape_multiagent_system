class Coordinator:
    def __init__(self, agents, negotiation_engine, conversation_log):
        self.agents = agents
        self.negotiation_engine = negotiation_engine
        self.conversation_log = conversation_log

    def run_round(self, story_state):
        story_context = story_state.get_full_story()

        print("\n--- AGENT COMMUNICATION ROUND ---")

        # ---- COMMUNICATION ROUND ----
        for agent in self.agents:
            message = agent.communicate(
                story_context,
                self.conversation_log.get()
            )
            self.conversation_log.add(agent.name, message)

            print(f"\n[{agent.name} says]:")
            print(message)

        print("\n--- END OF AGENT DISCUSSION ---")

        # ---- PROPOSAL ROUND ----
        proposals = {}
        for agent in self.agents:
            proposal = agent.propose(
                story_context,
                self.conversation_log.get()
            )
            proposals[agent.name] = proposal

        chosen_agent = self.negotiation_engine.select(proposals)

        return {
            "agent": chosen_agent,
            "text": proposals[chosen_agent]
        }
