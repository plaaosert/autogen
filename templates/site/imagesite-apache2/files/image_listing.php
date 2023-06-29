<?php
include "session.php";
?>

<html>
    <?php
    $title = 'Posts';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <div class="post-container">
            <?php
            $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "imagesite_data");
            if ($conn->connect_error) {
                die("Failed to load page. (sql error)");
            }

            $conn->set_charset("utf8mb4");

            try {
                $sql = "SELECT * FROM posts ORDER BY id DESC;";
                $stmt = $conn->prepare($sql);
                $stmt->execute();

                $result = $stmt->get_result();
                $stmt->close();

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