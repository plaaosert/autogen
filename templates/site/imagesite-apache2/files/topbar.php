<div class="topbar">
    <?php

    $path = $_SERVER["REQUEST_URI"];
    $basename = basename($path);

    echo '<a class="' . (($basename == "image_listing.php") ? "disabled" : "enabled") . '" href="image_listing.php">Home</a>';
    echo '<a class="' . (($basename == "profile.php") ? "disabled" : "enabled") . '" href="profile.php">Profile</a>';
    echo '<a class="' . (($basename == "login.php" || $basename == "register.php") ? "disabled" : "enabled") . '" href="' . ($logged_in_id ? "logout.php" : "login.php") . '">' . ($logged_in_id ? "Logout" : "Login") . '</a>';

    ?>

    <!--
    <div class="searchbox">
        <form action="/search_products.php">
            <input type="text" placeholder="Search for a product..." name="query">
            <button type="submit">Search</button>
        </form>
    </div>
    -->
</div>

<div class="pagebuffer">

</div>
