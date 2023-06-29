<?php
include "session.php";

$id = isset($_GET['postid']) ? (int)$_GET['postid'] : 0;
if (!$id) {
    header('Location: image_listing.php');
    exit();
}
?>

<html>
    <?php
    $title = 'View Post';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <div class="single-post-container">
            <?php
            $id = isset($_GET['postid']) ? (int)$_GET['postid'] : 0;

            $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "imagesite_data");
            if ($conn->connect_error) {
                die("Failed to load page.");
            }

            $conn->set_charset("utf8mb4");

            try {
                // to show a post, we need to get:
                // - the post caption
                // - the post image URL
                //
                // - the ID of the user who posted it
                // - the name of the user who posted it
                //
                // - all comments on the post
                // - the IDs and names of all users who posted

                $sql_post_info = "SELECT posts.id AS post_id, posts.author AS post_author, posts.caption AS post_caption, posts.img_url AS post_img_url, users.name AS author_name, COUNT(likes.post_id) AS like_count FROM ((posts INNER JOIN users ON posts.author = users.id) LEFT JOIN likes ON likes.post_id = posts.id) WHERE posts.id = ? GROUP BY posts.id, likes.post_id;";
                $stmt = $conn->prepare($sql_post_info);

                $stmt->bind_param("i", $id);

                $stmt->execute();

                $result = $stmt->get_result();
                $stmt->close();

                //var_dump($result);

                while ($row = $result->fetch_assoc()) {
                    $comments_sql = "SELECT comments.author AS comment_author, comments.content AS comment_content, users.name AS author_name FROM comments INNER JOIN users ON comments.author = users.id WHERE comments.post_id = ? ORDER BY comments.id DESC";
                    $comments_stmt = $conn->prepare($comments_sql);
                    $comments_stmt->bind_param("i", $id);

                    $comments_stmt->execute();

                    $comments_result = $comments_stmt->get_result();
                    $comments_stmt->close();

                    //var_dump($comments_result);

                    echo '<div class="post-entry">';
                    echo '  <img width=400px height=400px src="'. $row["post_img_url"] .'">';
                    echo '  <p class="post-caption">' . $row["post_caption"] . "</p>";

                    if ($logged_in_id) {
                        echo '  <p><a class="post-likes" href="add_like.php?postid=' . $id . '">❤ ' . $row["like_count"] . "</a></p>";
                    } else {
                        echo '  <p class="post-likes">❤ ' . $row["like_count"] . "</p>";
                    }

                    echo '  <a class="post-author" href="profile.php?userid=' . $row["post_author"] . '">' . $row["author_name"] . '</a>';
                    echo '</div><div class="comments-entry">';

                    if (isset($_SESSION["id"])) {
                        echo '<form action="/add_comment.php">';
                        echo '<input type="text" placeholder="Add a comment!" name="content">';
                        echo '<input type="hidden" name="postid" value="' . $id . '">';
                        echo '<button type="submit">Comment</button></form>';
                    }

                    $need_empty_dialog = 1;
                    while ($comments_row = $comments_result->fetch_assoc()) {
                        echo '<a class="comment-author" href="profile.php?userid=' . $comments_row["comment_author"] . '">' . $comments_row["author_name"] . '</a>';
                        echo '<p class="comment-content">' . $comments_row["comment_content"] . '</p>';

                        $need_empty_dialog = 0;
                    }

                    if ($need_empty_dialog) {
                        echo '<p class="comment-content" style="color:grey">No comments yet...</p>';
                    }

                    echo '</div>';
                }
            } catch (Exception $e) {
                die("Failed to load page.");
            }

            $conn->close();
            ?>
        </div>
    </body>
</html>