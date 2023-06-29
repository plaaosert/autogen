<?php
include "session.php";

if (!$logged_in_id) {
    header('Location: image_listing.php');
    exit();
} else {
    // check the name and pass hopefully supplied
    if (isset($_GET["postid"])) {
        $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "imagesite_data");
        if ($conn->connect_error) {
            die("Failed to load page.");
        }

        try {
            $post_id = $_GET["postid"];

            // first check if the post is liked or not by us
            $check_sql = "SELECT user_id, post_id FROM likes WHERE user_id=? AND post_id=?";
            $check_stmt = $conn->prepare($check_sql);

            $check_stmt->bind_param("ii", $logged_in_id, $post_id);

            $check_stmt->execute();
            $check_result = $check_stmt->get_result();
            $check_stmt->close();

            $liked = 0;
            while ($check_row = $check_result->fetch_assoc()) {
                $liked = 1;
            }

            $sql = "INSERT INTO likes (`user_id`, `post_id`) VALUES (?, ?);";
            if ($liked) {
                $sql = "DELETE FROM likes WHERE user_id=? AND post_id=?";
            }

            $stmt = $conn->prepare($sql);

            $stmt->bind_param("ii", $logged_in_id, $post_id);

            $stmt->execute();

            header('Location: view_image.php?postid=' . (int)$_GET["postid"]);
            $stmt->close();

            exit();
        } catch (Exception $e) {
            header('Location: view_image.php?postid=' . (int)$_GET["postid"]);
            exit();
        }

        $conn->close();
    } else {
        header('Location: image_listing.php');
        exit();
    }
}
?>

