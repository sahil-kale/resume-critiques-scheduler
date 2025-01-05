# Resume Critiques Scheduling Utility

I help run my school engineering society's termly resume critique event! Last term, we had to schedule over 600 participants, and doing this by hand was tedious.

This tool helps schedule participants and volunteers auto(magically) - it determines who is best to critique a resume by solving a score-based optimization problem, where a score is assigned by the amount of overlapping 'interests' between a participant and volunteer, as well as whether they are from the same program. It also enforces break conditions and ensures that a schedule honours a volunteers' and participants time constraints.

The result -> the entire 600+ event once required 2 extra individuals whose entire job was scheduling. Now, it's a simple `python3 scheduler.py` invocation. 