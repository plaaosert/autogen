import os
import random
import timeit

import autogen

autogen.set_loglevel(autogen.LOGLEVEL.CRITICAL)


def bench_full():
    difficulty = random.randint(5, 55)

    autogen.generate(difficulty)


def bench_build():
    difficulty = random.randint(5, 55)

    autogen.generate(difficulty, skip_health_check=True)


def bench_testautogen():
    base = autogen.BaseTemplate(
        "apache2-ubuntu", os.path.join("templates", "base", "apache2-ubuntu")
    )

    site = autogen.SiteTemplate(
        "testautogen-apache2", os.path.join("test-autogen", "template", "testautogen-apache2")
    )

    autogen.stage_and_start((base,), site, ())


benches = (
    ("Autogen", bench_testautogen),
    ("Build only", bench_build),
    ("Full deploy", bench_full)
)

print("Starting benchmark. May take some time.")

with open("bench_results_win_300523.txt", "w") as f:
    for bench in benches:
        time_taken = timeit.timeit(bench[1], number=25) / 25

        result = "{}: {}s".format(bench[0], time_taken)
        print(result)
        f.write(result + "\n")


print("Complete")
