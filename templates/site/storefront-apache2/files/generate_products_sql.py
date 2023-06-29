import random


def generate():
    name_prefixes = [
        ["Best", 2.6],
        ["100% Authentic", 3.4],
        ["100% Natural", 1.8],
        ["Exotic", 2.4],
        ["Best Value", 0.7],
        ["Trustworthy", 1.4],
        ["Legal", 6],
        ["Great Value", 0.8],
        ["Authentic", 2.6],
        ["Standard", 1],
        ["Cheap", 0.5],
        ["Luxury", 2.1],
        ["Real", 1.7],
        ["Pre-Owned", 0.6],
        ["Pre-Loved", 0.8],
        ["Refurbished", 0.9],
        ["Budget", 0.65],
        ["Folding", 1.25],
        ["Pre-Assembled", 1.2],
        ["Reliable", 1.1],
        ["Patented", 2],
        ["Heated", 1.8],
        ["Shiny", 2.2],
        ["Premium", 2.8],
        ["Award-Winning", 3],
        ["Miniature", 0.3],
        ["Portable", 1.2],
    ]

    name_materials = [
        ["Wooden", 1],
        ["Stone", 2],
        ["Rock", 2.2],
        ["Metal", 3.1],
        ["Steel", 4],
        ["Iron", 3],
        ["Birch Wood", 1.2],
        ["Oak Wood", 1.6],
        ["Coal", 0.4],
        ["Velvet", 2.3],
        ["Fur", 1.6],
        ["Plush", 2.2],
        ["Plastic", 0.7],
        ["Glass", 1.8],
        ["Stained Glass", 3.6],
        ["Sandstone", 1.4],
        ["Red", 1.1],
        ["Yellow", 1.1],
        ["Green", 1.11],
        ["Blue", 1.1],
        ["Multicolored", 1.2],
        ["Foam", 0.2],
        ["Cardboard", 0.1],
        ["Transparent", 1.3],
        ["Marble", 2.5],
    ]

    name_items = [
        ["Chair", 25],
        ["Table", 60],
        ["Armchair", 50],
        ["Desk", 100],
        ["Standing Desk", 160],
        ["Dining Table", 200],
        ["Cupboard", 60],
        ["Bed", 200],
        ["Dresser", 140],
        ["Lamp", 10],
        ["Coffee Table", 20],
        ["Bedside Table", 17],
        ["Bedside Cabinet", 16],
        ["TV Table", 55],
        ["Arcade Cabinet", 260],
        ["Kitchen Unit", 900],
        ["Sliding Door", 400],
        ["Window", 200],
        ["Trinket", 5],
        ["Gadget", 800],
        ["Pencil Sharpener", 10],
        ["Hammer", 10],
        ["Nails", 1],
        ["Cup Holder", 20],
        ["Kitchen Plate", 5],
        ["Car Seat", 100],
        ["Doorstop", 10],
        ["Toy", 8],
        ["Microwave", 70],
        ["Fridge", 80],
        ["Refrigerator", 80],
        ["Vacuum Cleaner", 110],
        ["Freezer", 90]
    ]

    check_outs = [
        "Check out this",
        "Don't miss out on this",
        "On sale now: the",
        "Only available online: the",
        "The",
        "The one and only",
        "Just in: the",
        "A new entry in the 2023 catalogue: the",
    ]

    taglines = [
        "Don't miss out!",
        "On sale now!",
        "On sale for a limited time only!",
        "Only 10 more in stock!",
        "Only available online!",
        "On sale for the lowest price ever!",
        "Lowest price ever!",
        "As seen on TV!",
        "Don't miss this once in a lifetime offer!",
        "A bestseller!",
        "Nominated for the \'Best Thing 2022\' award!",
    ]

    txt = ""
    names_picked = set()
    for i in range(random.randint(200, 500)):
        name = ""
        value = 1

        attempts = 0
        while (not name or name in names_picked) and attempts < 10:
            attempts += 1
            name = ""
            value = 1

            if random.randint(0, 1) == 0:
                c = random.choice(name_prefixes)
                name += "{} ".format(c[0])
                value *= c[1]

            c = random.choice(name_materials)
            name += "{} ".format(c[0])
            value *= c[1]

            c = random.choice(name_items)
            name += "{}".format(c[0])

            value = c[1] * value
            value *= random.randint(80, 120) / 100.0
            if value > 500:
                value = round(value / 25) * 25
            if value > 25:
                value = round(value / 5) * 5
            else:
                value = round(value)

            value = max(1, value)
            value -= 0.01

        if attempts < 10:
            txt += "(\"{}\", \"{} {}, available exclusively here. {}\", {}),\n".format(
                name, random.choice(check_outs), name.lower(), random.choice(taglines), value
            )

            names_picked.add(name)

    return txt[:-2]


if __name__ == "__main__":
    print(generate())
    # print("\n".join(sorted(generate().split("\n"), key=lambda t: float(t.split(", ")[-1].replace(")", "").replace(",", "")))))