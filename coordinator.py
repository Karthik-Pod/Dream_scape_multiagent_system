class Coordinator:
    def __init__(self, agents, negotiation_engine):
        self.agents = agents
        self.negotiation_engine = negotiation_engine

    def run_round(self, story_state):
        proposals = []

        for agent in self.agents:
            proposal = agent.generate_proposal(story_state)
            proposals.append(proposal)

        resolved = self.negotiation_engine.resolve(proposals)

        # debug visibility
        print("\nNegotiation summary:")
        for p in proposals:
            print(f"- {p['agent']} ({p['type']}) proposed")

        return resolved
