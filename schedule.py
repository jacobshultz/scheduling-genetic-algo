import copy
import random
from models import *

class Schedule: # AKA Chromosome
    periods: list[Period]

    def __init__(self, periods: list[Period]):
        self.periods = copy.deepcopy(periods)

    def __str__(self) -> str:
        msg = ""

        for p in self.periods:
            t = p.time if p.time < 13 else p.time - 12
            msg += f"Period: {t}\n{p}\n"

        return msg

    def count_courses(self) -> int:
        return len([rc for pd in self.periods for rc in pd.scheduled if rc.course is not None])

    def fill(self, courses: list[Course]):
        """Randomly garunteed-ly fills schedule with courses. Conforms to hard restrictions. Use to generate initial population."""

        for c in random.sample(courses, len(courses)):
            if not self._fill_one(c):
                raise ValueError(f"Cannot find slot for course: {c.name}")

    def _fill_one(self, c: Course, seen: set[tuple[int, int, int]] | None = None, depth: int = 0) -> bool:
        if seen is None:
            seen = set()

        if depth > len(self.periods) * 3:   # hard max-bound to prevent infinite recursion issues
            return False

        candidate_periods = [p for p in random.sample(self.periods, len(self.periods))]

        # try to place into any empty slot
        for p in candidate_periods:
            if p.try_fit(c, nice=True) == True:
                return True

        # try a displacement move
        for p in candidate_periods:
            snapshot = copy.deepcopy(self)
            res = p.try_fit(c)
            if res == True:
                return True
            if type(res) is Course:
                loop_key = (c.id, p.time, res.id)
                if loop_key in seen:    # we've been here before. Restore to previous valid state
                    self.periods = snapshot.periods
                    continue

                seen.add(loop_key)
                child = copy.deepcopy(self)
                if child._fill_one(res, seen, depth + 1):
                    self.periods = child.periods
                    return True

                self.periods = snapshot.periods

        return False

    def swap(self, new_pds: list[Period]):
        """Swap out a period, reschedule orphaned classes. For crossover."""

        # search entire shedule for each new course, wipe when found
        # safe to wipe since, we are going to reinsert in the next step
        for n_pd in new_pds:
            for o_pd in self.periods:
                for n_rc in n_pd.scheduled:
                    if n_rc.course is not None:     # at least you know I didn't vibecode this assignment
                        for o_rc in o_pd.scheduled:
                            if o_rc.course is not None and n_rc.course.id == o_rc.course.id:
                                o_rc.course = None
                                break

        # litterally swap the existing periods with their new counterparts
        for n_pd in new_pds:
            for o_pd in self.periods:
                if n_pd.time == o_pd.time:
                    orphans = o_pd.swap(n_pd)   # when we swap we might accrue casualties,
                                                # scheduling prioritizes the anatomy of n_pd
                    
                    # now re-fit the orphans randomly
                    r_orphs = random.sample(orphans, len(orphans)) if len(orphans) > 0 else []
                    nice: bool = True
                    while len(r_orphs) > 0:
                        success: bool = False
                        crnt = r_orphs.pop()
                        for pd in random.sample(self.periods, len(self.periods)):
                            success = pd.try_fit(crnt, nice=nice) # type: ignore
                            if success: break

                        if not (nice or success): raise ValueError("Faield to re-fit an orphaned class.")
                        nice = success

            

    def score(self):
        score = 0
        last_class_at: int = -1
        prof_schedule = {}
        for p in self.periods: # for each timeslot
            for rc in p.scheduled:  # for room
                if rc.course is not None:   # course at this time
                    # penalty for delay between classes
                    delay = p.time - last_class_at
                    if last_class_at != -1 and delay > 2 :
                        score -= (delay - 2 ) * 15
                    last_class_at = p.time

                    # record schedule for professor
                    p_r_key = rc.course.prof.id
                    prof_schedule.setdefault(p_r_key, []).append((rc.room.id, p.time))

                    # size underutilized penalty
                    score -= rc.room.size - rc.course.size


        for p_schedule in prof_schedule.values():
            last_room_id: int = -1
            last_break: int = 8
            last_worked: int = 8

            for (room_id, time) in p_schedule:
                # overworked penalty
                if last_worked + 1 != time:
                    last_break = time - 1
                
                last_worked = time

                working_streak = time - last_break
                if working_streak >= 3:
                    score -= (working_streak - 2) * 10

                # room streak bonus
                if last_room_id == room_id:
                    score += 5
                
                last_room_id = room_id

        self._got_score = True
        return score