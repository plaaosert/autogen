<?php
include "session.php";

// AA access
if (!$logged_in_id) {
    header('Location: /');
    exit();
}
// AA access END
?>

<html>
    <?php
    $title = 'Admin';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <p>This is the admin area</p>
        <p>There's nothing here...</p>
        <a href="employee_logout.php">Log out</a>
    </body>
</html>