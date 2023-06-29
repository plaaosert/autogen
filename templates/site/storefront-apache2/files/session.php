<?php

// Place error reporting enabling here

session_start();

$logged_in_id = isset($_SESSION["id"]) ? $_SESSION["id"] : 0;

?>