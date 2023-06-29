import autogen

# Monkey patch the log() function so it pipes into a buffer which we can use for testing
log_buffer = []

autogen.log = lambda loglevel, *objects, prefix="UNKNOWN", suffix="\u001b[0m": None if loglevel == autogen.LOGLEVEL.DEBUG or loglevel == autogen.LOGLEVEL.INFO else (log_buffer.append("{} ".format(
    loglevel
) + "{} ".format(
    prefix
) + ", ".join(
    str(o) for o in objects
)), "print(loglevel, prefix, " ".join(objects))")

autogen.log_error = lambda loglevel, *objects: autogen.log(loglevel, *objects, prefix="ERROR")
autogen.log_failure = lambda loglevel, *objects: autogen.log(loglevel, *objects, prefix="FAILURE")
autogen.log_success = lambda loglevel, *objects: autogen.log(loglevel, *objects, prefix="SUCCESS")
autogen.log_info = lambda loglevel, *objects: autogen.log(loglevel, *objects, prefix="INFO")


# generate(15, forced_bases=("apache2",), forced_vulns=("imagesite",))
# difficulty: none, out of 0-100 range, 100 (no vulns), 15 (should work), set with forced vuln
# forced_bases: none, invalid base, one right one wrong, one valid, two valid
# forced_site : none, forced site, incompatible site with forced vuln
# forced_vulns: none, one vuln, incompatible vuln with forced site

tests = [
    (
        "No parameters",
        lambda: autogen.generate(skip_health_check=True),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Valid difficulty",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15),
        (
            ("SUCCESS", ""),
        )
    ),

    (
        "Difficulty with no valid challenges",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=90),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Difficulty out of range",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=999),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Forced vuln with valid difficulty set",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_vulns=("sqli-search",)),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Valid forced base with valid difficulty",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_bases=("apache2",)),
        (
            ("SUCCESS", ""),
        )
    ),

    (
        "Forced base invalid",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_bases=("INVALID!",)),
        (
            ("ERROR", ""),
        )
    ),

    (
        "One valid forced base, one invalid",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_bases=("apache2", "INVALID!",)),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Two valid forced bases",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_bases=("apache2", "mysql",)),
        (
            ("SUCCESS", ""),
        )
    ),

    (
        "Two forced bases of the same type",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_bases=("apache2", "apache2",)),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Valid forced site",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_site="storefront"),
        (
            ("SUCCESS", ""),
        )
    ),

    (
        "Invalid forced site",
        lambda: autogen.generate(skip_health_check=True, chosen_difficulty=15, forced_site="INVALID!"),
        (
            ("ERROR", ""),
        )
    ),

    (
        "One valid vuln",
        lambda: autogen.generate(skip_health_check=True, forced_vulns=("storefront-sqli-loginform-blind",)),
        (
            ("SUCCESS", ""),
        )
    ),

    (
        "Same vuln twice",
        lambda: autogen.generate(skip_health_check=True, forced_vulns=("imagesite-fileupload-normal", "imagesite-fileupload-normal")),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Valid forced site with compatible vuln",
        lambda: autogen.generate(skip_health_check=True, forced_site="storefront", forced_vulns=("storefront-sqli-loginform-blind",)),
        (
            ("SUCCESS", ""),
        )
    ),

    (
        "Valid forced site with incompatible vuln",
        lambda: autogen.generate(skip_health_check=True, forced_site="imagesite", forced_vulns=("storefront-sqli-loginform-blind",)),
        (
            ("ERROR", ""),
        )
    ),

    (
        "Forced bases, site, vuln, all compatible",
        lambda: autogen.generate(skip_health_check=True, forced_bases=("apache2",), forced_site="storefront", forced_vulns=("storefront-sqli-loginform-blind",)),
        (
            ("SUCCESS", ""),
        )
    ),
]

# print("\n".join(
#     "{} & {} &  & \cellcolor[[[{}!10]]]{} & \cellcolor[[[green!30]]]Yes \\\\\n"
#     "\\hline".format(
#         ind+1, tests[ind][0],
#         {"SUCCESS": "green", "ERROR": "red"}[tests[ind][2][0][0]],
#         tests[ind][2][0][0]
#     ).replace("[[[", "{").replace("]]]", "}") for ind in range(len(tests))
# ))

for testid, test in enumerate(tests):
    log_buffer.clear()

    test_success = False
    test_result = ""

    print("({:3}/{:<3}) {:48} | ".format(
        testid+1, len(tests), test[0]
    ), end="")

    try:
        test[1]()

        # check the buffer
        type_counts = {}
        for condition in test[2]:
            log_num = type_counts.get(condition[0], 0)

            search_log_num = 0
            new_test_result = "not enough {} logs".format(condition[0])

            for log in log_buffer:
                log_segs = log.split(" ", 2)

                if log_segs[1] == condition[0]:
                    if search_log_num == log_num:
                        if condition[1] in log_segs[2]:
                            test_success = True
                            break
                        else:
                            new_test_result = "{} not in {}".format(
                                condition[1], log_segs[2]
                            )
                            break

                    search_log_num += 1

            test_result = new_test_result + "  "
    except Exception as e:
        test_result = "exception"
        test_success = False

    if test_success:
        print("PASS")
    else:
        print("FAIL ({})".format(
            test_result.rstrip()
        ))

    #print("")
