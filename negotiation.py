class NegotiationEngine:
    def select(self, proposals: dict) -> str:
        """
        No role priority.
        All agents are equal.
        Selection based on content contribution.
        """

        # simple, deterministic, neutral selection
        # (longer proposal usually means richer contribution)
        return max(proposals, key=lambda agent: len(proposals[agent]))
