<?php
include "session.php";

$query = isset($_GET['query']) ? $_GET['query'] : 0;
if (!$query) {
    header('Location: product_listing.php');
    exit();
}
?>

<html>
    <?php
    $title = 'Search Results';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <div class="search-results">
            <?php
                $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "storefront_data");
                if ($conn->connect_error) {
                    die("Failed to load page.");
                }

                try {
                    $searchterm = $conn->real_escape_string($query);

                    $sql = "SELECT * FROM products WHERE name LIKE '%$searchterm%';";
                    //echo $sql;

                    $stmt = $conn->prepare($sql);
                    $stmt->execute();

                    $result = $stmt->get_result();
                    $stmt->close();

                    $nr = $result->num_rows;
                    echo '<h1 class="search-num-results">Found ' . $nr . ' product' . ($nr == 1 ? '' : 's') . '</h1>';

                    while ($row = $result->fetch_assoc()) {
                        echo '<div class="search-result">';
                        echo '  <div class="search-image"><a href="show_product.php?productid=' . $row["id"] . '"><img width=120px height=120px src="images/productimg.png"></a></div>';
                        echo '  <div class="search-text"><a href="show_product.php?productid=' . $row["id"] . '" class="search-result-name">' . $row["name"] . "</a>";
                        echo '  <p class="search-product-price">£' . $row["price"] . "</p></div>";
                        echo "</div>";
                    }
                } catch (Exception $e) {
                    die("Failed to load page.");
                }

                $conn->close();
            ?>
        </div>
    </body>
</html>