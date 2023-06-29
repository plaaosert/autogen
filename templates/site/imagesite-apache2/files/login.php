<?php
include "session.php";

if ($logged_in_id) {
    header('Location: profile.php');
    exit();
}
?>

<html>
    <?php
    $title = 'Login';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <p>If you already have an account, log in below.</p>
        <form action="/login_form.php">
            <input type="text" placeholder="Username" name="name">
            <input type="password" placeholder="Password" name="pass">
            <button type="submit">Login</button>
        </form>
        <?php
        if (isset($_GET["incorrect"]) && $_GET["incorrect"]) {
            echo "<p style='color:red'>Incorrect username or password</p>";
        }
        ?>
        <p>If you don't have an account, you can <a href="register.php">register</a> for one now.</p>
    </body>
</html>