<div class="topbar">
    <?php

    $path = $_SERVER["REQUEST_URI"];
    $basename = basename($path);

    echo '<a class="' . (($basename == "product_listing.php") ? "disabled" : "enabled") . '" href="product_listing.php">Products</a>';
    echo '<a class="' . (($basename == "contact_form.php") ? "disabled" : "enabled") . '" href="contact_form.php">Contact</a>';
    echo '<a class="' . (($basename == "employee_login.php" || $basename == "admin_area.php") ? "disabled" : "enabled") . '" href="employee_login.php">' . ($logged_in_id ? "Employee Area" : "Employee Login") . '</a>';

    ?>

    <div class="searchbox">
        <form action="/search_products.php">
            <input type="text" placeholder="Search for a product..." name="query">
            <button type="submit">Search</button>
        </form>
    </div>
</div>

<div class="pagebuffer">

</div>
