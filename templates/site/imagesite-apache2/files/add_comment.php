<?php
include "session.php";

if (!$logged_in_id) {
    header('Location: image_listing.php');
    exit();
} else {
    // check the name and pass hopefully supplied
    if (isset($_GET["postid"]) && isset($_GET["content"])) {
        $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "imagesite_data");
        if ($conn->connect_error) {
            die("Failed to load page.");
        }

        try {
            $sql = "INSERT INTO comments (`post_id`, `author`, `content`) VALUES (?, ?, ?);";
            $stmt = $conn->prepare($sql);

            $post_id = $_GET["postid"];
            $content = $_GET["content"];

            $stmt->bind_param("iis", $post_id, $logged_in_id, $content);

            $stmt->execute();

            if ($stmt->affected_rows > 0) {
                // post success
                header('Location: view_image.php?postid=' . (int)$_GET["postid"]);
                exit();
            } else {
                header('Location: view_image.php?postid=' . (int)$_GET["postid"]);
                exit();
            }

            $stmt->close();
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

