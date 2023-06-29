import hashlib
import random
import string


def generate():
    # deliberately use rockyou words so that the pass hashes could possibly be cracked
    rockyou_words = [
        "hello",
        "elizabeth",
        "hottie",
        "tinkerbell",
        "charlie",
        "samantha",
        "barbie",
        "chelsea",
        "lovers",
        "teamo",
        "jasmine",
        "brandon",
        "666666",
        "shadow",
        "melissa",
        "eminem",
        "matthew",
        "robert",
        "danielle",
        "forever",
        "family",
        "jonathan",
        "987654321",
        "computer",
        "whatever",
        "dragon",
        "vanessa",
        "cookie",
        "naruto",
        "summer",
        "sweety",
        "spongebob",
        "joseph",
        "junior",
        "softball",
        "taylor",
        "yellow",
        "daniela",
        "lauren",
        "mickey",
        "princesa",
        "alexandra",
        "alexis",
        "jesus",
        "estrella",
        "miguel",
        "william",
        "thomas",
        "beautiful",
        "mylove",
        "angela",
        "poohbear",
        "patrick",
        "iloveme",
        "sakura",
        "adrian",
        "alexander",
        "destiny",
        "christian",
        "121212",
        "sayang",
        "america",
        "dancer",
        "monica",
        "richard",
        "112233",
        "princess1",
        "555555",
        "diamond",
        "carolina",
        "steven",
        "rangers",
        "louise",
        "orange",
        "789456",
        "999999",
        "shorty",
        "11111",
        "nathan",
        "snoopy",
        "gabriel"
    ]

    st = random.choice(rockyou_words)

    return "INSERT INTO `employee_logins` (`name`, `pass`) VALUES\n" \
           "('admin', '{}');".format(
        hashlib.sha512(st.encode("utf-8")).hexdigest()
    )


if __name__ == "__main__":
    print(generate())
