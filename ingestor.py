import csv
import re

from datatypes import EventParticipant, EventPeople

def Ingest(volunteer_filepath, critiquees_filepath) -> EventPeople:
    event_people = EventPeople()

    with open(volunteer_filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # skip the header
        next(reader)
        for row in reader:
            name = row[1]
            email = row[2]
            program = row[4]
            interests = row[5]
            availability = row[6]
            event_people.volunteers.append(EventParticipant(name, program, email, interests, availability))

    with open(critiquees_filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            name = row[1]
            email = row[2]
            program = row[4]
            interests = row[5]
            availability = row[6]
            event_people.participants.append(EventParticipant(name, program, email, interests, availability))
        
    return event_people

if __name__ == '__main__':
    event_people = Ingest('sample_data/volunteers.csv', 'sample_data/participants.csv')
    breakpoint()