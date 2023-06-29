<?php
include "session.php";

if ($logged_in_id) {
    header('Location: admin_area.php');
    exit();
}
?>

<html>
    <?php
    $title = 'Employee Login';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <p>If you have a valid username and password for logging into the site, use it here.</p>
        <form action="/employee_login_form.php">
            <input type="text" placeholder="Username" name="name">
            <input type="password" placeholder="Password" name="pass">
            <button type="submit">Login</button>
        </form>
        <?php
        if (isset($_GET["incorrect"]) && $_GET["incorrect"]) {
            echo "<p style='color:red'>Incorrect username or password</p>";
        }
        ?>
    </body>
</html>