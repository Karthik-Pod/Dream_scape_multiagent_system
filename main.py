from story_state import StoryState
from character_agent import  CharacterAgent
from emotion_agent import EmotionAgent
from plot_agent import PlotAgent
from negotiation import NegotiationEngine
from coordinator import Coordinator
from conversation import ConversationLog 
def main():
    prompt = input("Enter story prompt: ")
    state = StoryState(prompt)

    agents = [
        PlotAgent(),
        CharacterAgent(),
        EmotionAgent()]
    
    conversation_log = ConversationLog()
   
    coordinator = Coordinator(
        agents=agents,
        negotiation_engine=NegotiationEngine(),
        conversation_log = conversation_log
        )

    for _ in range(3):
        chosen = coordinator.run_round(state)
        state.add_segment(chosen["text"])
        print(f"Chosen: {chosen['agent']}")

    print("\nFinal Story:")
    print(state.get_full_story())

if __name__ == "__main__":
    main()
