from dataclasses import dataclass
import hyperparams as hp
from typing import Self
import copy
import random

@dataclass
class GenInfo:
    num: int
    min: int
    avg: int
    max: int

@dataclass
class Room:
    id: int
    name: str
    size: int
    multimedia: bool

@dataclass
class Professor:
    id: int
    name: str

@dataclass
class Course:
    id: int
    name: str
    prof: Professor
    size: int
    multimedia: bool

@dataclass
class _RoomCourse:
    room: Room
    course: Course | None

class Period:   # AKA gene
    id: int
    time: int
    scheduled: list[_RoomCourse]

    def __init__(self, id: int, time: int, rooms: list[Room]) -> None:
        self.id = id
        self.time = time
        self.scheduled = []
        for r in rooms:
            self.scheduled.append(_RoomCourse(r, None))

    def __str__(self) -> str:
        msg = ""
        for rc in self.scheduled:
            msg += f"Room: {rc.room.name} ({rc.room.size}), "
            if rc.course is not None:
                msg += f"Course: {rc.course.name} ({rc.course.size}), Prof: {rc.course.prof.name}"
            else: msg += "Course: None"
            msg += "\n"

        return msg

    # checks hard requirements
    def _check_hard_reqs(self, r: Room, c: Course) -> bool:
        return self._check_rc_relation(r, c) and len(self._find_timeslot_conflicts(c)) == 0

    def _check_rc_relation(self, r: Room, c: Course) -> bool:
        return (
            c.size <= r.size
        ) and (
            not c.multimedia or r.multimedia
        )

    def _find_timeslot_conflicts(self, c: Course) -> list[_RoomCourse]:
        # list comp checks to see if course already is in timeslot or if professor is already in timeslot.
        return [rc for rc in self.scheduled if rc.course is not None and (c.id == rc.course.id or c.prof.id == rc.course.prof.id)] 

    def try_fit(self, n_course: Course, nice: bool = False) -> Course | bool:
        """Try to insert course into period. Return displaced course OR true for clean success, false for failure to fit.
        """
        rand_scheduled = random.sample(self.scheduled, len(self.scheduled))
        for rc in rand_scheduled:   # check open slots first
            if rc.course is None and self._check_hard_reqs(rc.room, n_course):
                rc.course = n_course
                return True

        for rc in rand_scheduled:   # no open slots, must swap
            if (rc.course is not None and not nice) and self._check_hard_reqs(rc.room, n_course):
                displaced = rc.course
                rc.course = n_course
                return displaced # type: ignore

        return False    # if we get here then it is impossible to fit the course in this timeslot

    def swap(self, n_pd: Self) -> list[Course]:
        "Hard-swaps period for a different one. Passes in orphaned courses."
        if self.time != n_pd.time:
            raise ValueError("Tried to swap two periods at different times.")

        orphans: list[Course] = []
        for n_rc in n_pd.scheduled:
            if n_rc.course is not None:
                # wipe conflicts for now
                for conflict in self._find_timeslot_conflicts(n_rc.course):
                    orphans.append(conflict.course) #type: ignore
                    conflict.course = None

            for o_rc in self.scheduled:
                if o_rc.room.id == n_rc.room.id:
                    if o_rc.course is not None: orphans.append(o_rc.course)
                    o_rc.course = n_rc.course

        self.scheduled = copy.deepcopy(n_pd.scheduled)
        # orphans will get recycled by the schedule
        return orphans