import re
import datetime

class EventParticipant :
    def __init__(self, name, program, email, interests, availability):
        self.name = name
        self.program = program
        self.email = email
        self.interests = self.convert_interests_to_string_list(interests)
        self.availability = self.convert_availabilities_to_string_list(availability)
        self.num_critiques = 0

    def convert_availabilities_to_string_list(self, availabilities):
        parts = re.split(r",(?![^()]*\))", availabilities)
        # Clean up any extra spaces
        parts = [p.strip() for p in parts]

        avail_interval = []

        for part in parts:
            start_time, end_time = part.split(" - ")
            start_time = datetime.datetime.strptime(start_time, "%I:%M %p").time()
            end_time = datetime.datetime.strptime(end_time, "%I:%M %p").time()
            avail_interval.append((start_time, end_time))

        return avail_interval

    def is_time_in_availability(self, time):
        for interval in self.availability:
            if interval[0] <= time < interval[1]:
                return True
        return False

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