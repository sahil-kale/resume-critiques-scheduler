import argparse
import click
import datetime
import random
from enum import Enum

from ingestor import Ingest
from datatypes import EventPeople, EventParticipant


class Critique:
    """
    Represents a single critique slot, which can be scheduled for a participant with a volunteer.
    """

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
        """
        Initialize a critique slot.

        :param schedule_status: The status of the critique (OPEN_NOT_SCHEDULED, SCHEDULED, or NOT_AVAILABLE).
        :param volunteer: The volunteer for this critique slot.
        :param time: The time of this critique slot (datetime.time).
        """
        self.schedule_status = schedule_status
        self.volunteer = volunteer
        self.time = time
        self.participant = None

    def schedule(self, participant):
        """
        Schedules this critique with the given participant and updates volunteer/participant counters.
        """
        self.participant = participant
        self.schedule_status = Critique.CritiqueScheduleStatus.SCHEDULED

        # Initialize volunteer's list if needed
        if not hasattr(self.volunteer, "scheduled_critiques"):
            self.volunteer.scheduled_critiques = []

        self.volunteer.scheduled_critiques.append(self)
        self.volunteer.num_critiques += 1
        self.participant.num_critiques += 1

    def __str__(self):
        """
        Returns a string representation of the critique slot, including volunteer, participant, time, and status.
        """
        participant_name = self.participant.name if self.participant else "None"
        return (
            f"Critique {self.schedule_status}. "
            f"Volunteer: {self.volunteer.name}, "
            f"Participant: {participant_name}, "
            f"Time: {self.time.strftime('%I:%M %p')}"
        )


class Scheduler:
    """
    Manages the scheduling of participants and volunteers for an event, creating critiques at defined intervals,
    then assigning participants based on matching scores and availability.
    """

    def __init__(self, event_people, start_time, end_time, critique_time_interval_minutes):
        """
        Initializes the Scheduler.

        :param event_people: An EventPeople object containing volunteers and participants.
        :param start_time: Start time (string in '%I:%M %p' format).
        :param end_time: End time (string in '%I:%M %p' format).
        :param critique_time_interval_minutes: Interval in minutes for each critique slot.
        """
        self.event_people = event_people
        self.start_time = datetime.datetime.strptime(start_time, "%I:%M %p").time()
        self.end_time = datetime.datetime.strptime(end_time, "%I:%M %p").time()
        # We allow scheduling to run slightly after end time (by 15 mins).
        self.scheduling_end_time = (
            datetime.datetime.combine(datetime.datetime.today(), self.end_time)
            + datetime.timedelta(minutes=15)
        ).time()

        self.critique_time_interval_minutes = critique_time_interval_minutes
        self.schedule_matrix = []  # Stores all Critique objects

    def run(self):
        """
        Builds a schedule matrix of open critique slots, assigns participants, and then handles postprocessing.
        """
        # Step 1: Build the schedule matrix with open slots.
        num_schedulable_critiques = self._build_schedule_matrix()
        click.secho(
            f"Number of schedulable critiques for event: {num_schedulable_critiques}. Number of participants: {len(self.event_people.participants)}",
            fg="green",
        )

        # Step 2: Assign participants to the best available Critique slot.
        self._assign_participants()

        # Remove unused (not scheduled) critiques.
        self.schedule_matrix = [
            critique
            for critique in self.schedule_matrix
            if critique.schedule_status == Critique.CritiqueScheduleStatus.SCHEDULED
        ]
        click.secho(
            f"Number of critiques scheduled: {len(self.schedule_matrix)}",
            fg="green",
        )
        click.secho(
            f"Number of participants without a critique: {len(self.participants_without_schedule)}",
            fg="red"
        )

        # Step 3: Postprocessing – for instance, apply breaks or adjust times for overbooked volunteers.
        self._postprocess_schedule_for_breaks()

    def _build_schedule_matrix(self):
        """
        Creates open critique slots for all volunteers who are available at each time interval
        from the start_time to the end_time.

        :return: The number of total open (schedulable) critique slots created.
        """
        num_schedulable_critiques = 0
        schedule_time = datetime.datetime.combine(datetime.datetime.today(), self.start_time)
        end_time_dt = datetime.datetime.combine(datetime.datetime.today(), self.end_time)

        while schedule_time < end_time_dt:
            for volunteer in self.event_people.volunteers:
                # Check if this volunteer is available at this time.
                if volunteer.is_time_in_availability(schedule_time.time()):
                    critique = Critique(
                        Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED,
                        volunteer,
                        schedule_time.time(),
                    )
                    self.schedule_matrix.append(critique)
                    num_schedulable_critiques += 1

            schedule_time += datetime.timedelta(minutes=self.critique_time_interval_minutes)

        return num_schedulable_critiques

    def _assign_participants(self):
        """
        For each participant, find the best open critique slot based on availability and a matching score,
        then schedule it if found. Otherwise, notify that no slot was found.
        """
        self.participants_without_schedule = []
        for participant in self.event_people.participants:
            best_open_critique = None
            best_score = -99999

            for critique in self.schedule_matrix:
                if (
                    critique.schedule_status == Critique.CritiqueScheduleStatus.OPEN_NOT_SCHEDULED
                    and participant.is_time_in_availability(critique.time)
                ):
                    score = self.calculate_score(participant, critique.volunteer)
                    if score > best_score:
                        best_score = score
                        best_open_critique = critique

            # Schedule the participant in the best found slot if available.
            if best_open_critique:
                best_open_critique.schedule(participant)
            else:
                self.participants_without_schedule.append(participant)

    def _postprocess_schedule_for_breaks(self):
        """
        Adjusts schedules for volunteers who exceed a certain number of critiques. Here, if a volunteer
        has >= 5 critiques, randomly pick a critique slot (except the first) and push it by 15 minutes.
        """

        for volunteer in self.event_people.volunteers:
            # If volunteer has 5 or more scheduled critiques, add a "break"
            if volunteer.num_critiques >= 5:
                random_critique_index = random.randint(1, len(volunteer.scheduled_critiques) - 1)
                critique_to_move = volunteer.scheduled_critiques[random_critique_index]

                critique_time = datetime.datetime.combine(
                    datetime.datetime.today(), critique_to_move.time
                )
                new_time = (critique_time + datetime.timedelta(minutes=15)).time()
                critique_to_move.time = new_time

    def calculate_score(self, participant, volunteer):
        """
        Calculates a "match score" for a participant-volunteer pairing based on:
          - % overlap in interests
          - Matching program
          - Current number of critiques the volunteer already has scheduled

        :param participant: The participant to be matched.
        :param volunteer: The volunteer to be matched.
        :return: A floating-point score indicating the strength of the match.
        """
        participant_interests = set(participant.interests)
        volunteer_interests = set(volunteer.interests)
        common_interests = participant_interests.intersection(volunteer_interests)

        # Avoid division by zero if a volunteer has no interests defined.
        participant_interest_common = (
            len(common_interests) / len(participant_interests)
            if len(participant_interests) != 0
            else 0
        )
        volunteer_interest_common = (
            len(common_interests) / len(volunteer_interests)
            if len(volunteer_interests) != 0
            else 0
        )

        # Add a bonus if both volunteer and participant are in the same program.
        program_match = 1 if participant.program == volunteer.program else 0

        # We penalize a volunteer who has many critiques scheduled already by subtracting volunteer.num_critiques.
        return (participant_interest_common + volunteer_interest_common) * 3 + program_match * 2 - volunteer.num_critiques

    def print_schedule_matrix(self):
        """
        Prints the entire schedule matrix (only the scheduled critiques after run()) to the console.
        """
        for critique in self.schedule_matrix:
            click.secho(str(critique), fg="cyan")

    def write_schedule_to_csv(self, schedule_filename, unavailable_filename):
        """
        Writes the schedule matrix to a CSV file with volunteers as rows and time slots as columns.

        :param schedule_filename: The name of the output CSV file.
        """
        time_header = []
        time_header_times = []
        current_time = datetime.datetime.combine(datetime.datetime.today(), self.start_time)

        # Build the time header up until the scheduling end time.
        while current_time.time() < self.scheduling_end_time:
            time_header.append(current_time.strftime("%I:%M %p"))
            time_header_times.append(current_time.time())
            current_time += datetime.timedelta(minutes=self.critique_time_interval_minutes)

        with open(schedule_filename, "w") as f:
            f.write(f"Volunteer,{','.join(time_header)}\n")

            for volunteer in self.event_people.volunteers:
                row_cells = [volunteer.name]
                for t in time_header_times:
                    critique = next(
                        (
                            c
                            for c in self.schedule_matrix
                            if c.volunteer == volunteer and c.time == t
                        ),
                        None,
                    )
                    participant_name = critique.participant.name if critique else ""
                    row_cells.append(participant_name)
                f.write(",".join(row_cells) + "\n")

        with open(unavailable_filename, "w") as f:
            f.write(f"Participant,Email\n")
            for participant in self.participants_without_schedule:
                f.write(f"{participant.name},{participant.email}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Schedule participants and volunteers for an event"
    )
    parser.add_argument("volunteers", help="Path to a CSV file containing volunteers")
    parser.add_argument("participants", help="Path to a CSV file containing participants")
    args = parser.parse_args()

    event_people = Ingest(args.volunteers, args.participants)
    scheduler = Scheduler(event_people, "6:30 PM", "9:15 PM", 15)
    scheduler.run()
    #scheduler.print_schedule_matrix()
    scheduler.write_schedule_to_csv("schedule.csv", "unscheduled.csv")


if __name__ == "__main__":
    # seed random number generator for reproducibility
    random.seed(42)
    main()
