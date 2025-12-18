class StoryState:
    def __init__(self, initial_prompt):
        self.initial_prompt = initial_prompt
        self.story = [initial_prompt]
        self.round = 0

    def add_segment(self, text):
        self.story.append(text)
        self.round += 1

    def get_full_story(self):
        return " ".join(self.story)

    def get_last_segment(self):
        if len(self.story) > 1:
            return self.story[-1]
        return self.initial_prompt

    def get_round(self):
        return self.round
