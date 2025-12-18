class NegotiationEngine:
    ROLE_PRIORITY = {
        "character": 3,
        "plot": 2,
        "emotion": 1
    }

    def resolve(self, proposals):
        # sort proposals by role dominance
        sorted_props = sorted(
            proposals,
            key=lambda p: self.ROLE_PRIORITY.get(p.get("type"), 0),
            reverse=True
        )

        primary = sorted_props[0]
        merged_text = primary["text"]

        # merge secondary contributions
        for prop in sorted_props[1:]:
            if prop["type"] == "plot":
                merged_text += " " + prop["text"]
            elif prop["type"] == "emotion":
                merged_text += " " + prop["text"]

        return {
            "agent": primary["agent"],
            "text": merged_text,
            "type": "merged"
        }
