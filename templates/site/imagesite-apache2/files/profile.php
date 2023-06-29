<?php
include "session.php";

$id = isset($_GET['userid']) ? (int)$_GET['userid'] : 0;
if (!$id) {
    if (isset($_SESSION['id'])) {
        $id = $_SESSION['id'];
    } else {
        header('Location: login.php');
        exit();
    }
}
?>

<html>
    <?php
    $title = 'Profile';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <div class="single-post-container">
            <?php
            $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "imagesite_data");
            if ($conn->connect_error) {
                die("Failed to load page. (sql error)");
            }

            $conn->set_charset("utf8mb4");

            try {
                $profile_sql = "SELECT id, name FROM users WHERE id = ?";
                $profile_stmt = $conn->prepare($profile_sql);
                $profile_stmt->bind_param("i", $id);

                $profile_stmt->execute();

                $profile_result = $profile_stmt->get_result();
                $profile_stmt->close();

                $profile_row = $profile_result->fetch_assoc();

                echo '<b><p class="profile-name">' . $profile_row["name"] . '</p></b>';


                $sql = "SELECT * FROM posts WHERE author = ? ORDER BY id DESC;";
                $stmt = $conn->prepare($sql);

                $stmt->bind_param("i", $id);

                $stmt->execute();

                $result = $stmt->get_result();
                $stmt->close();

                echo '<p class="profile-info">' . $result->num_rows . ' posts</p></b><br>';

                if (!isset($_GET['userid'])) {
                    echo '<b><p>Post a new image...</p></b>';
                    echo '<form action="/post_image.php" method="post" enctype="multipart/form-data">';
                    echo '<input type="file" name="file">';
                    echo '<input type="text" placeholder="Caption" name="caption">';
                    echo '<button type="submit">Post</button>';
                    echo '</form>';
                }

                echo '</div><div class="post-container">';

                while ($row = $result->fetch_assoc()) {
                    $likes_sql = "SELECT COUNT(post_id) AS like_count FROM likes WHERE post_id = ?";
                    $likes_stmt = $conn->prepare($likes_sql);
                    $likes_stmt->bind_param("i", $row["id"]);

                    $likes_stmt->execute();

                    $likes_result = $likes_stmt->get_result();
                    $likes_stmt->close();

                    $likes_row = $likes_result->fetch_assoc();


                    $user_sql = "SELECT id, name FROM users WHERE id = ?";
                    $user_stmt = $conn->prepare($user_sql);
                    $user_stmt->bind_param("i", $row["author"]);

                    $user_stmt->execute();

                    $user_result = $user_stmt->get_result();
                    $user_stmt->close();

                    $user_row = $user_result->fetch_assoc();

                    echo '<div class="post-entry">';
                    echo '  <a href="view_image.php?postid=' . $row["id"] . '"><img width=120px height=120px src="' . $row["img_url"] . '"></a><br>';
                    echo '  <div class="post-footer"><a class="post-author" href="profile.php?userid=' . $row["author"] . '">' . $user_row["name"] . "</a>";
                    echo '  <p class="post-likes">❤ ' . $likes_row["like_count"] . '</p></div>';
                    echo '</div>';
                }
            } catch (Exception $e) {
                header('Location: register.php?incorrect=true');
                exit();
            }

            $conn->close();
            ?>
        </div>
    </body>
</html>