from ingestor import Ingest
from datatypes import EventPeople, EventParticipant
import argparse
import click
import datetime
from enum import Enum
import random

class Critique:
    class CritiqueScheduleStatus(Enum):
        OPEN_NOT_SCHEDULED = 1
        SCHEDULED = 2
        NOT_AVAILABLE = 3

        def __str__(self):
            if self == Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED:
                return "OPEN - NOT SCHEDULED"
            elif self == Critique.CritiqueScheduleStatus.SCHEDULED:
                return "SCHEDULED"
            elif self == Critique.CritiqueScheduleStatus.NOT_AVAILABLE:
                return "NOT AVAILABLE"

    def __init__(self, schedule_status, volunteer, time):
        self.schedule_status = schedule_status
        self.volunteer = volunteer
        self.time = time
        self.participant = None

    def schedule(self, participant):
        self.participant = participant
        self.schedule_status = Critique.CritiqueScheduleStatus.SCHEDULED
        if self.volunteer.num_critiques == 0:
            self.volunteer.scheduled_critiques = []

        self.volunteer.scheduled_critiques.append(self)
        
        self.volunteer.num_critiques += 1
        self.participant.num_critiques += 1
        

    def __str__(self):
        return f"Critique {self.schedule_status}. Volunteer: {self.volunteer.name}, Participant: {self.participant.name}, Time: {self.time}"


class Scheduler:
    def __init__(self, event_people, start_time, end_time, critique_time_interval_minutes):
        self.start_time = datetime.datetime.strptime(start_time, "%I:%M %p").time()
        self.end_time = datetime.datetime.strptime(end_time, "%I:%M %p").time()
        self.event_people = event_people
        self.critique_time_interval_minutes = critique_time_interval_minutes
        self.schedule_matrix = []

    def run(self):
        num_schedulable_critiques = 0
        schedule_time = datetime.datetime.combine(datetime.datetime.today(), self.start_time)
        end_time_dt = datetime.datetime.combine(datetime.datetime.today(), self.end_time)
        while schedule_time < end_time_dt:

            for volunteer in self.event_people.volunteers:
                if volunteer.is_time_in_availability(schedule_time.time()):
                    critique_schedule_status = Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED
                    num_schedulable_critiques += 1
                
                    critique = Critique(critique_schedule_status, volunteer, schedule_time.time())
                    self.schedule_matrix.append(critique)

            schedule_time += datetime.timedelta(minutes=self.critique_time_interval_minutes)
        
        click.secho(f"Number of schedulable critiques for event: {num_schedulable_critiques}", fg='green')

        for participant in self.event_people.participants:
            # iterate over the entire schedule matrix and find the best volunteer for each participant.
            best_open_critique = None
            best_score = 0
            for critique in self.schedule_matrix:
                is_participant_time_available = participant.is_time_in_availability(critique.time)
                is_critique_open = critique.schedule_status == Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED
                if is_critique_open and is_participant_time_available:
                    score = self.calculate_score(participant, critique.volunteer)
                    if score > best_score:
                        best_score = score
                        best_open_critique = critique
            
            if best_open_critique:
                best_open_critique.schedule(participant)
            else:
                click.secho(f"No available critiques for participant {participant.name}!", fg='red')

        # to account for breaks, first delete all critiques that are not scheduled
        self.schedule_matrix = [critique for critique in self.schedule_matrix if critique.schedule_status == Critique.CritiqueScheduleStatus.SCHEDULED]
        click.secho(f"Number of critiques scheduled: {len(self.schedule_matrix)}", fg='green')

        for volunteer in self.event_people.volunteers:
            if volunteer.num_critiques >= 5:
                random_critique_index = random.randint(1, len(volunteer.scheduled_critiques) - 1)
                for i in range(random_critique_index, len(self.schedule_matrix)):
                    critique = self.schedule_matrix[i]
                    critique_time = datetime.datetime.combine(datetime.datetime.today(), critique.time)
                    critique.time = (critique_time + datetime.timedelta(minutes=15)).time()


    def calculate_score(self, participant, volunteer):
        # calculate the score for a participant and volunteer by determining the % of interests that match for both the participant and volunteer
        participant_interests = set(participant.interests)
        volunteer_interests = set(volunteer.interests)

        common_interests = participant_interests.intersection(volunteer_interests)

        participant_interest_common = 0
        if len(participant_interests) != 0:
            participant_interest_common = len(common_interests) / len(participant_interests)
        volunteer_interest_common = len(common_interests) / len(volunteer_interests)

        program_match = 1 if participant.program == volunteer.program else 0

        return (participant_interest_common + volunteer_interest_common) * 3 + program_match * 2 - volunteer.num_critiques

    def print_schedule_matrix(self):
        for critique in self.schedule_matrix:
            click.secho(critique, fg="cyan")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Schedule participants and volunteers for an event')
    parser.add_argument('volunteers', help='Path to a CSV file containing volunteers')
    parser.add_argument('participants', help='Path to a CSV file containing participants')
    args = parser.parse_args()

    event_people = Ingest(args.volunteers, args.participants)
    scheduler = Scheduler(event_people, "6:30 PM", "9:15 PM", 15)
    scheduler.run()
    scheduler.print_schedule_matrix()