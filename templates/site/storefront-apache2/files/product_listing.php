<?php
include "session.php";
?>

<html>
    <?php
    $title = 'Product Listing';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <div class="product-container">
            <?php
            $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "storefront_data");
            if ($conn->connect_error) {
                die("Failed to load page.");
            }

            try {
                $sql = "SELECT * FROM products;";
                $stmt = $conn->prepare($sql);
                $stmt->execute();

                $result = $stmt->get_result();
                $stmt->close();

                while ($row = $result->fetch_assoc()) {
                    echo '<div class="product-entry">';
                    echo '  <a href="show_product.php?productid=' . $row["id"] . '"><img width=120px height=120px src="images/productimg.png"></a><br>';
                    echo '  <a href="show_product.php?productid=' . $row["id"] . '" class="product-name">' . $row["name"] . "</a>";
                    echo '  <p class="product-price">£' . $row["price"] . "</p>";
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