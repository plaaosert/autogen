<?php
include "session.php";

if ($logged_in_id) {
    header('Location: profile.php');
    exit();
} else {
    // check the name and pass hopefully supplied
    if (isset($_GET["name"]) && isset($_GET["pass"])) {
        $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "imagesite_data");
        if ($conn->connect_error) {
            die("Failed to load page.");
        }

        try {
            $sql = "INSERT INTO users (`name`, `password`) VALUES (?, ?);";
            $stmt = $conn->prepare($sql);

            $user = $_GET["name"];
            $pass = $_GET["pass"];
            $pass_hash = hash("sha512", $pass);

            $stmt->bind_param("ss", $user, $pass_hash);

            $stmt->execute();

            if ($stmt->affected_rows > 0) {
                // login success
                // get user ID now
                $_SESSION["id"] = $stmt->insert_id;

                header('Location: profile.php');
                exit();
            } else {
                header('Location: register.php?incorrect=true');
                exit();
            }

            $stmt->close();
        } catch (Exception $e) {
            header('Location: register.php?incorrect=true');
            exit();
        }

        $conn->close();
    } else {
        header('Location: image_listing.php');
        exit();
    }
}
?>

