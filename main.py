# type: ignore
from misc import *
import hyperparams as hp
from models import *
from schedule import *
from ga import *
import copy
import sys
import matplotlib.pyplot as plt
from datetime import datetime
import csv

print(f"GA Started at {datetime.now()}")

# cmdline args
args = sys.argv[1:]

if len(args) > 0:
    hp.POPULATION_SIZE = int(args[0])
if len(args) > 1:
    hp.MAX_GENERATIONS = int(args[1])
if len(args) > 2:
    hp.CROSSOVER_PROB = float(args[2])
if len(args) > 3:
    hp.MUTATION_PROB = float(args[3])
if len(args) > 4:
    hp.SELECTION_METHOD = args[4]
if len(args) > 5:
    hp.DEBUG = False if int(args[5]) == 0 else True

print(f"Parameters are: N={hp.POPULATION_SIZE}, Max Gens={hp.MAX_GENERATIONS}, Pc={hp.CROSSOVER_PROB}, Pm={hp.MUTATION_PROB}, Selection: {"tourna" if hp.SELECTION_METHOD == 'a' else "eliete"}")

# initialize the required models
rooms = [
    Room(1, 'BL134', 30, True),
    Room(2, 'BL138', 50, True),
    Room(3, 'KR224', 40, False),
    Room(4, 'KR206', 30, True),
    Room(5, 'Biddle123', 35, False),
    Room(6, 'Biddle205', 45, False),
    Room(7, 'ES100', 100, True)
]

periods = [
    Period(1, 9, rooms),
    Period(2, 10, rooms),
    Period(3, 11, rooms),
    Period(4, 12, rooms),
    Period(5, 13, rooms),
    Period(6, 14, rooms),
    Period(7, 15, rooms)
]

profs = [
    Professor(1, 'Bilitski'),
    Professor(2, 'Ohl'),
    Professor(3, 'Sandro'),
    Professor(4, 'Mr xxx'),
    Professor(5, 'Frederick'),
    Professor(6, 'Peter'),
    Professor(7, 'Brian'),
    Professor(8, 'Meg'),
    Professor(9, 'Stewie'),
    Professor(10, 'Glen')
]

courses = [
    Course(1, 'cs456', get_item(1, profs), 20, True),
    Course(2, 'cs456', get_item(1, profs), 20, True),
    Course(3, 'cs1783', get_item(1, profs), 15, True),
    Course(4, 'cs455', get_item(2, profs), 20, True),
    Course(5, 'cs455', get_item(2, profs), 20, True),
    Course(6, 'cs015', get_item(3, profs), 35, True),
    Course(7, 'cs015', get_item(4, profs), 35, False),
    Course(8, 'cs015', get_item(4, profs), 35, False),
    Course(9, 'cs015', get_item(5, profs), 35, False),
    Course(10, 'math001', get_item(6, profs), 40, False),
    Course(11, 'math001', get_item(6, profs), 50, False),
    Course(12, 'math001', get_item(6, profs), 60, False),
    Course(13, 'math002', get_item(7, profs), 40, False),
    Course(14, 'math002', get_item(7, profs), 50, False),
    Course(15, 'math002', get_item(7, profs), 60, False),
    Course(16, 'Soc100', get_item(8, profs), 45, True),
    Course(17, 'Soc100', get_item(8, profs), 40, True),
    Course(18, 'Soc100', get_item(8, profs), 35, True),
    Course(19, 'CS047', get_item(9, profs), 15, True),
    Course(20, 'CS047', get_item(9, profs), 15, True),
    Course(21, 'PSY200', get_item(10, profs), 30, False),
    Course(22, 'PSY200', get_item(10, profs), 35, False),
    Course(23, 'PSY200', get_item(10, profs), 30, False),
    Course(24, 'cs045', get_item(2, profs), 20, True),
    Course(25, 'cs045', get_item(2, profs), 20, True),
    Course(26, 'cs015', get_item(3, profs), 20, True)
]

# generate initial population
population: list[Schedule] = []
for i in range(hp.POPULATION_SIZE):
    s = Schedule(copy.deepcopy(periods))
    s.fill(courses)
    population.append(s) 

# run GA loop
best = (copy.deepcopy(population[0]), 1)
generation = 0
gen_data = []

while generation < hp.MAX_GENERATIONS:
    generation += 1

    if (hp.MAX_GENERATIONS > 500 and generation % 500 == 0) or (hp.MAX_GENERATIONS <= 500 and generation % 100 == 0):
        print(f"Generation {generation} at {datetime.now()}")
    else:
        debug(f"Generation {generation} at {datetime.now()}")

    # record metrics
    fitnesses = []
    for s in population:
        fitness = s.score()
        fitnesses.append(fitness)
        if fitness > best[0].score():
            best = (copy.deepcopy(s), generation)

    info = GenInfo(generation, min(fitnesses), sum(fitnesses)/len(fitnesses), max(fitnesses))
    gen_data.append(info)
    debug(f"\tMin fitness: {info.min}")
    debug(f"\tAvg fitness: {info.avg}")
    debug(f"\tMax fitness: {info.max}")

    # generate next generation
    new_population = []
    while len(new_population) < len(population):
        p1 = select(population)
        p2 = select(population)

        c = try_cross(p1, p2)
        try_mutate(c)
        new_population.append(c)

    population = new_population

# print
#offset = gen_data[0].min    # scale low end to it is closer to 0
offset = 0      # preserve original fitness score
print(f"GA has reached target generations ({hp.MAX_GENERATIONS}) at {datetime.now()}")
print("")
print(f"Best schedule recorded of fitness score: {best[0].score() - offset} in generation {best[1]}. See details below.")
print("")
print(best[0])
if best[0].count_courses() < len(courses):
    raise ValueError("Best schedule does not include all courses.")

# output data to csv
with open(f"{hp.POPULATION_SIZE}_{hp.CROSSOVER_PROB}_{hp.MUTATION_PROB}_{hp.SELECTION_METHOD}.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Generation", "Min Fitness", "Avg Fitness", "Max Fitness"])
    for info in gen_data:
        writer.writerow([info.num, info.min, info.avg, info.max])

# plot
x = list(range(generation))
y_avgs = [info.avg - offset for info in gen_data]
y_mins = [info.min - offset for info in gen_data]
y_maxs = [info.max - offset for info in gen_data]

line, = plt.plot(x, y_avgs, label="Avg Fitness", color="blue")
line_min, = plt.plot(x, y_mins, label="Min Fitness", color="red")
line_max, = plt.plot(x, y_maxs, label="Max Fitness", color="green")
plt.legend()
plt.xlabel("Generation")
plt.ylabel("Fitness")
plt.title(f"N: {hp.POPULATION_SIZE}, Pc: {hp.CROSSOVER_PROB}, Pm: {hp.MUTATION_PROB}, Selection: {"tourna" if hp.SELECTION_METHOD == 'a' else "eliete"}")

plt.savefig(f"{hp.POPULATION_SIZE}_{hp.CROSSOVER_PROB}_{hp.MUTATION_PROB}_{hp.SELECTION_METHOD}.png")
plt.show(block=True)