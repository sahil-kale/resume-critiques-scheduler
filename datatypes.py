import re

class EventParticipant :
    def __init__(self, name, program, email, interests, availability):
        self.name = name
        self.program = program
        self.email = email
        self.interests = self.convert_interests_to_string_list(interests)
        self.availability = self.convert_availabilities_to_string_list(availability)

    def convert_availabilities_to_string_list(self, availabilities):
        parts = re.split(r",(?![^()]*\))", availabilities)
        # Clean up any extra spaces
        parts = [p.strip() for p in parts]

        return parts

    def convert_interests_to_string_list(self, interests):
        parts = re.split(r",(?![^()]*\))", interests)
        # Clean up any extra spaces
        parts = [p.strip() for p in parts]

        return parts
    
    def __str__(self):
        return f"{self.name} ({self.program}) - {self.email} - {self.interests} - {self.availability}"

class EventPeople:
    def __init__(self):
        self.participants = []
        self.volunteers = []