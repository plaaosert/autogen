<?php
include "session.php";

if ($logged_in_id) {
    header('Location: profile.php');
    exit();
}
?>

<html>
    <?php
    $title = 'Register';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <p>Register for a new account here.</p>
        <form action="/register_form.php">
            <input type="text" placeholder="Username" name="name">
            <input type="password" placeholder="Password" name="pass">
            <button type="submit">Login</button>
        </form>
        <?php
        if (isset($_GET["incorrect"]) && $_GET["incorrect"]) {
            echo "<p style='color:red'>Your chosen username is already taken</p>";
        }
        ?>
        <p>If you already have an account, you can <a href="login.php">login</a>.</p>
    </body>
</html>