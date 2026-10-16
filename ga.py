import copy
from misc import debug
from models import *
from schedule import *
import hyperparams as hp

# scoring is implemented as a method of the schedule object

def select(pool: list[Schedule]) -> Schedule:
    if hp.SELECTION_METHOD == 'a':
        return _select_tourna(pool)
    else:
        return _select_eliete(pool)

def _select_tourna(pool: list[Schedule]) -> Schedule:
    a = random.randint(0, len(pool) -1)
    b = random.randint(0, len(pool) -1)
    if pool[a].score() > pool[b].score():
        return pool[a]
    else:
        return pool[b]

def _select_eliete(pool: list[Schedule]) -> Schedule:   # randomly select from top 20% of population
    sorted_pool = sorted(pool, key=lambda s: s.score(), reverse=True)
    top_20 = sorted_pool[:max(1, int(len(sorted_pool) * 0.20))]
    return random.choice(top_20)

def try_cross(a: Schedule, b: Schedule) -> Schedule:
    if random.random() >= hp.CROSSOVER_PROB: return a

    pt = random.randrange(1, len(a.periods))

    c = copy.deepcopy(a)
    if random.random() < 0.5:
        c.swap(copy.deepcopy(b.periods[pt:]))
    else:
        c.swap(copy.deepcopy(b.periods[:pt]))

    return c

def try_mutate(a: Schedule):
    if random.random() >= hp.MUTATION_PROB: return

    done = False
    while(not done):
        pd = random.choice(a.periods)
        courses = [rc for rc in pd.scheduled if rc.course is not None]
        if len(courses) == 0:
            continue

        rc = random.choice(courses)
        winner = rc.course
        rc.course = None

        a.fill([winner]) # type: ignore
        done = True
