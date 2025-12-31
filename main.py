from story_state import StoryState
from agent import PlotAgent, CharacterAgent,EmotionAgent
from negotiation import NegotiationEngine
from coordinator import Coordinator
def main():
    prompt = input("Enter story prompt: ")
    state = StoryState(prompt)

    agents = [
        PlotAgent("PlotAgent", "plot", 1.0),
        CharacterAgent("CharacterAgent", "character", 0.2),
        EmotionAgent("EmotionAgent", "emotion", 0.5)
]
    coordinator = Coordinator(
        agents=agents,
        negotiation_engine=NegotiationEngine()
    )

    for _ in range(3):
        chosen = coordinator.run_round(state)
        state.add_segment(chosen["text"])
        print(f"Chosen: {chosen['agent']}")

    print("\nFinal Story:")
    print(state.get_full_story())

if __name__ == "__main__":
    main()
