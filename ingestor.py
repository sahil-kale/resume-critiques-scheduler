import csv
import re

from datatypes import EventParticipant, EventPeople

def Ingest(volunteer_filepath, critiquees_filepath, date_available_filter) -> EventPeople:
    event_people = EventPeople()

    with open(volunteer_filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # skip the header
        next(reader)
        for row in reader:
            name = row[1]
            email = row[2]
            dates_available = row[3]
            program = row[4]
            interests = row[5]
            availability = row[6]
            event_people.volunteers.append(EventParticipant(name, program, email, interests, availability, dates_available))

    with open(critiquees_filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            name = row[1]
            email = row[2]
            dates_available = row[3]
            program = row[4]
            interests = row[5]
            availability = row[6]
            event_people.participants.append(EventParticipant(name, program, email, interests, availability, dates_available))
    
    # only return event volunteers and participants if the dates available is "Resume Critique 1 - Jan 13"
    event_people.participants = [p for p in event_people.participants if p.dates_available == date_available_filter]
    #event_people.volunteers = [v for v in event_people.volunteers if v.dates_available == date_available_filter]

    return event_people

if __name__ == '__main__':
    event_people = Ingest('sample_data/volunteers.csv', 'sample_data/participants.csv')