import hashlib
import random
import string
from typing import List


CLIQUE_STRENGTH = 2


snames = (
     "SMITH",
     "JONES",
     "WILLIAMS",
     "TAYLOR",
     "BROWN",
     "DAVIES",
     "EVANS",
     "WILSON",
     "THOMAS",
     "JOHNSON",
     "ROBERTS",
     "ROBINSON",
     "THOMPSON",
     "WRIGHT",
     "WALKER",
     "WHITE",
     "EDWARDS",
     "HUGHES",
     "GREEN",
     "HALL",
     "LEWIS",
     "HARRIS",
     "CLARKE",
     "PATEL",
     "JACKSON",
     "WOOD",
     "TURNER",
     "MARTIN",
     "COOPER",
     "HILL",
     "WARD",
     "MORRIS",
     "MOORE",
     "CLARK",
     "LEE",
     "KING",
     "BAKER",
     "HARRISON",
     "MORGAN",
     "ALLEN",
     "JAMES",
     "SCOTT",
     "PHILLIPS",
     "WATSON",
     "DAVIS",
     "PARKER",
     "PRICE",
     "BENNETT",
     "YOUNG",
     "GRIFFITHS"
)


def ascii_render_post(post):
    return "\"{}\"\n" \
           "- {} (liked by {})\n\n" \
           "{}".format(
        post.caption,
        post.author_obj.name,
        ", ".join(post.likes[liker].name for liker in post.likes.keys()),
        "\n".join("{}: {}".format(
            post.comments[commenter][1].name, post.comments[commenter][0]) for commenter in post.comments.keys()
        )
    )


def generate_username(users):
    while True:
        choice = "{}.{}.{}".format(
            random.choice(string.ascii_lowercase), random.choice(snames).lower(), random.randint(1, 50000)
        )

        if not any(user.name == choice for user in users):
            return choice


def generate_password():
    st = "".join(random.choice(string.ascii_lowercase) for _ in range(32))
    return hashlib.sha512(st.encode("utf-8")).hexdigest()


def generate_caption():
    return random.choice((
        "loving it",
        "wish you were here",
        "my favourite view",
        "<3",
        "...",
        "i dont want to leave",
        "beautiful place",
        "holiday",
        "yknow",
        "hey there"
    ))


def generate_comment():
    text = random.choice((
        "I love this",
        "My favourite",
        "In love",
        "You look great",
        "Stunning",
        "Amazing",
        "Love it",
        "Beautiful",
        "Adorable",
        "<3",
        "OMG",
        "omggg",
        ":OOO"
    ))

    exclamations = "!" * random.choice((0, 0, 0, 1, 1, 2, 3))

    emojis = "".join(random.choice((
        "😍",
        "😍😍",
        "🥰",
        "🤗",
        "😲",
        "😘",
        "👀",
        "😻",
        "💥",
        "💯",
        "🔥",
        "❤",
        "💕",
        "💜",
        "💝",
        "💖",
        "✨",
        "💞"
    )) for _ in range(random.randint(0, 3)))

    return "{}{} {}".format(text, exclamations, emojis)


def generate():
    # first, generate a set of users who will "simulate" posting, liking and commenting
    class Post:
        id_inc = 1

        def __init__(self, author_obj, caption, image_url):
            self.post_id = Post.id_inc
            Post.id_inc += 1

            self.author_obj = author_obj
            self.author_id = author_obj.user_id
            self.caption = caption
            self.image_url = image_url

            self.likes = {}
            self.comments = {}

        def like(self, by):
            #print("user \"{}\" liked post id \"{}\"".format(by.name, self.post_id))

            self.likes[by.user_id] = by
            self.author_obj.gain_affinity(by, 1)

        def been_liked(self, by):
            return by.user_id in self.likes

        def can_like(self, by):
            return not self.been_liked(by) and self.author_id != by.user_id

        def comment(self, by, txt):
            #print("user \"{}\" commented on post id \"{}\"".format(by.name, self.post_id))

            self.comments[by.user_id] = [txt, by]
            self.author_obj.gain_affinity(by, 3)

        def been_commented(self, by):
            return by.user_id in self.comments

        def can_comment(self, by):
            return not self.been_commented(by) and self.author_id != by.user_id

    class User:
        id_inc = 1

        def __init__(self, name, password, activity, post_chance, like_chance, comment_chance):
            self.user_id = User.id_inc
            User.id_inc += 1

            self.name = name
            self.password = password
            self.activity = activity
            self.post_chance = post_chance
            self.like_chance = like_chance
            self.comment_chance = comment_chance

            self.affinity = {}

        def get_affinity(self, to, real=False):
            if to.user_id in self.affinity:
                return int(pow(self.affinity[to.user_id] + 1, 1 if real else CLIQUE_STRENGTH))
            else:
                return 1

        def gain_affinity(self, to, amt):
            if to.user_id in self.affinity:
                self.affinity[to.user_id] += amt
            else:
                self.affinity[to.user_id] = amt

        def action_step(self, posts: List[Post]):
            # check if we do anything at all
            if random.random() < self.activity:
                # check chance to like a post. do so repeatedly until our chance unrolls or no more exist
                liking = True
                while liking and random.random() < self.like_chance:
                    like_candidates = list(filter(lambda post: post.can_like(self), posts))
                    like_choices = []
                    for post in like_candidates:
                        # print("[like] adding post \"{}\" {} times".format(post.post_id, self.get_affinity(post.author_obj)))
                        like_choices.extend(
                            [post for _ in range(self.get_affinity(post.author_obj))]
                        )

                    if len(like_choices) > 0:
                        # pick 3 posts, choose the latest one (highest ID number)
                        targets = [random.choice(like_choices) for _ in range(3)]
                        target = max(targets, key=lambda p: p.post_id)

                        target.like(self)
                    else:
                        liking = False

                # check chance to comment on a post. same rules as liking
                commenting = True
                while commenting and random.random() < self.comment_chance:
                    comment_candidates = list(filter(lambda post: post.can_comment(self), posts))
                    comment_choices = []
                    for post in comment_candidates:
                        # print("[comment] adding post \"{}\" {} times".format(post.post_id, self.get_affinity(post.author_obj)))
                        comment_choices.extend(
                            [post for _ in range(self.get_affinity(post.author_obj))]
                        )

                    if len(comment_candidates) > 0:
                        # pick 3 posts, choose the latest one (highest ID number)
                        targets = [random.choice(comment_choices) for _ in range(3)]
                        target = max(targets, key=lambda p: p.post_id)

                        text = generate_comment()

                        target.comment(self, text)

                        # if we can like it, do that
                        if target.can_like(self):
                            target.like(self)
                    else:
                        commenting = False

                # check chance to post. if we do, return the new post
                if random.random() < self.post_chance:
                    new_post = Post(self, generate_caption(), "uploads/img{}.png".format(random.randint(1, 9)))

                    return new_post

    users = []
    for _ in range(10):
        users.append(User(generate_username(users), generate_password(), 0.05, 0.015, 0.1, 0.04))

    posts = []

    for step in range(10000):
        if step % 750 == 0:
            users.append(User(generate_username(users), generate_password(), 0.05, 0.015, 0.1, 0.04))

        #print("\n -- iteration {} --".format(step + 1))
        for user in users:
            post = user.action_step(posts)
            if post:
                # print("user \"{}\" posted post id {}".format(user.name, post.post_id))
                posts.append(post)

    if False:
        print("\n-----\n")

        for user in users:
            print("\n".join(
                "{} ={}> <{}= {}".format(
                    user.name, user.get_affinity(other, True), other.get_affinity(user, True), other.name
                ) for other in filter(lambda u: u.user_id != user.user_id, users)
            ))
            print("---")

        print("")
        print("{} posts\n".format(len(posts)))
        input("")

        for post in posts:
            print(ascii_render_post(post))
            print("---")

        input("")

    # now actually make the template!
    template = "INSERT INTO `users` (`name`, `password`) VALUES\n" \
               "{};\n\n" \
               "INSERT INTO `posts` (`author`, `caption`, `img_url`) VALUES\n" \
               "{};\n\n" \
               "INSERT INTO `likes` (`user_id`, `post_id`) VALUES\n" \
               "{};\n\n" \
               "INSERT INTO `comments` (`post_id`, `author`, `content`) VALUES\n" \
               "{};\n\n"

    users_insert = "\n".join(
        "('{}', '{}'),".format(
            user.name, user.password
        ) for user in users
    )

    posts_insert = "\n".join(
        "('{}', '{}', '{}'),".format(
            post.author_id, post.caption, post.image_url
        ) for post in posts
    )

    likes_insert = ""
    for post in posts:
        likes_insert += "".join(
            "('{}', '{}'),\n".format(
                like, post.post_id
            ) for like in post.likes.keys()
        )

    comments_insert = ""
    for post in posts:
        comments_insert += "".join(
            "('{}', '{}', '{}'),\n".format(
                post.post_id, comment, post.comments[comment][0]
            ) for comment in post.comments.keys()
        )

    return template.format(
        users_insert[:-1],
        posts_insert[:-1],
        likes_insert[:-2],
        comments_insert[:-2]
    )


if __name__ == "__main__":
    print(generate())
