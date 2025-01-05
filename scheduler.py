from ingestor import Ingest
from datatypes import EventPeople, EventParticipant
import argparse
import click
from enum import Enum

TIMINGS = [
    "6:30 - 7:30 PM",
    "7:30 - 8:30 PM",
    "8:30 - 9:30 PM",
]

class Critique:
    class CritiqueScheduleStatus(Enum):
        OPEN_NOT_SCHEDULED = 1
        SCHEDULED = 2
        NOT_AVAILABLE = 3

    def __init__(self, schedule_status, volunteer):
        self.schedule_status = schedule_status
        self.volunteer = volunteer
        assert (schedule_status is Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED) or (schedule_status is Critique.CritiqueScheduleStatus.NOT_AVAILABLE)

        self.participant = None

    def schedule(self, participant):
        self.participant = participant
        self.schedule_status = Critique.CritiqueScheduleStatus.SCHEDULED

    def __str__(self):
        return f"Critique {self.schedule_status}. Volunteer: {self.volunteer.volunteer_data.name}, Participant: {self.participant}"

class Volunteer():
    def __init__(self, event_participant):
        self.volunteer_data = event_participant
        self.appointments = []

    def construct_appointment_slots(self, interval_minutes):
        # create a list of time slots for the volunteer
        SLOTS_PER_TIMESLICE = 60/interval_minutes

        for time in TIMINGS:
            if time in self.volunteer_data.availability:
                critique_schedule_status = Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED
            else:
                critique_schedule_status = Critique.CritiqueScheduleStatus.NOT_AVAILABLE
            
            for i in range(int(SLOTS_PER_TIMESLICE)):
                self.appointments.append(Critique(critique_schedule_status, self))

    def has_appointment_available(self):
        for appointment in self.appointments:
            if appointment.schedule_status is Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED:
                return True
        return False
    
    def get_next_available_appointment(self):
        for appointment in self.appointments:
            if appointment.schedule_status is Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED:
                return appointment
        return None

    def __str__(self):
        str_data = f"Volunteer {self.volunteer_data.name}\n"

        for appointment in self.appointments:
            str_data += f"\t{appointment}\n"

        return str_data


class Scheduler:
    def __init__(self, event_people, critique_time_interval_minutes):
        self.event_people = event_people
        self.critique_time_interval_minutes = critique_time_interval_minutes

    def schedule(self):
        volunteers = [Volunteer(x) for x in self.event_people.volunteers]
        for volunteer in volunteers:
            volunteer.construct_appointment_slots(self.critique_time_interval_minutes)
        
        for participant in self.event_people.participants:
            top_volunteer_choice = None
            top_volunteer_choice_score = 0

            for volunteer in volunteers:
                if volunteer.has_appointment_available():
                    score = self.calculate_score(participant, volunteer)
                    if score > top_volunteer_choice_score:
                        top_volunteer_choice = volunteer
                        top_volunteer_choice_score = score

            if top_volunteer_choice is not None:
                appointment = top_volunteer_choice.get_next_available_appointment()
                appointment.schedule(participant)
            else:
                click.echo(f"No available volunteers for participant {participant.name}", err=True)

                

    def calculate_score(self, participant, volunteer):
        # calculate the score for a participant and volunteer by determining the % of interests that match for both the participant and volunteer
        participant_interests = set(participant.interests)
        volunteer_interests = set(volunteer.volunteer_data.interests)

        common_interests = participant_interests.intersection(volunteer_interests)

        participant_interest_common = 0
        if len(participant_interests) != 0:
            participant_interest_common = len(common_interests) / len(participant_interests)
        volunteer_interest_common = len(common_interests) / len(volunteer_interests)

        program_match = 1 if participant.program == volunteer.volunteer_data.program else 0

        return (participant_interest_common + volunteer_interest_common) * 3 + program_match


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Schedule participants and volunteers for an event')
    parser.add_argument('volunteers', help='Path to a CSV file containing volunteers')
    parser.add_argument('participants', help='Path to a CSV file containing participants')
    args = parser.parse_args()

    event_people = Ingest(args.volunteers, args.participants)
    scheduler = Scheduler(event_people, critique_time_interval_minutes=15)
    scheduler.schedule()