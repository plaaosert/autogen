<?php
include "session.php";

if ($logged_in_id) {
    header('Location: admin_area.php');
    exit();
} else {
    // check the name and pass hopefully supplied
    if (isset($_GET["name"]) && isset($_GET["pass"])) {
        $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "storefront_data");
        if ($conn->connect_error) {
            die("Failed to load page.");
        }

        try {
            $sql = "SELECT id FROM employee_logins WHERE name=? AND pass=?;";
            $stmt = $conn->prepare($sql);

            $user = $_GET["name"];
            $pass = $_GET["pass"];
            $pass_hash = hash("sha512", $pass);

            $stmt->bind_param("ss", $user, $pass_hash);

            $stmt->execute();

            $result = $stmt->get_result();
            $stmt->close();

            if ($result->num_rows > 0) {
                // login success
                $_SESSION["id"] = $result->fetch_assoc()["id"];

                header('Location: admin_area.php');
                exit();
            } else {
                header('Location: employee_login.php?incorrect=true');
                exit();
            }
        } catch (Exception $e) {
            die("Failed to load page.");
        }

        $conn->close();
    } else {
        header('Location: product_listing.php');
        exit();
    }
}
?>

