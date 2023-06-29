<?php
include "session.php";

if ($logged_in_id) {
    unset($_SESSION["id"]);
}

header('Location: product_listing.php');
?>

