from story_state import StoryState
from agent import PlotAgent, CharacterAgent, EmotionAgent
from negotiation import NegotiationEngine
from coordinator import Coordinator

def main():
    prompt = input("Enter story prompt: ")

    # ✅ THIS LINE MUST EXIST
    state = StoryState(prompt)

    agents = [
        PlotAgent("PlotAgent", "plot", 0.6),
        CharacterAgent("CharacterAgent", "character", 0.9),
        EmotionAgent("EmotionAgent", "emotion", 0.5),
    ]

    negotiation_engine = NegotiationEngine()
    coordinator = Coordinator(agents, negotiation_engine)

    rounds = 3
    for _ in range(rounds):
        chosen = coordinator.run_round(state)
        state.add_segment(chosen["text"])

    print("\nFinal Story:")
    print(state.get_full_story())

if __name__ == "__main__":
    main()
