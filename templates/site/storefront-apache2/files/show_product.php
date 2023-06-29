<?php
include "session.php";

$id = isset($_GET['productid']) ? (int)$_GET['productid'] : 0;
if (!$id) {
    header('Location: product_listing.php');
    exit();
}
?>

<html>
    <?php
    $title = 'Product Display';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <div class="single-product-container">
            <?php
            $id = isset($_GET['productid']) ? (int)$_GET['productid'] : 0;

            $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "storefront_data");
            if ($conn->connect_error) {
                die("Failed to load page.");
            }

            try {
                $sql = "SELECT * FROM products WHERE id=?;";
                $stmt = $conn->prepare($sql);

                $stmt->bind_param("i", $id);

                $stmt->execute();

                $result = $stmt->get_result();
                $stmt->close();

                while ($row = $result->fetch_assoc()) {
                    echo '<div class="product-entry">';
                    echo '  <img width=400px height=400px src="images/productimg.png">';
                    echo '  <p class="product-name">' . $row["name"] . "</p>";
                    echo '  <p class="product-price">£' . $row["price"] . "</p>";
                    echo '  <p class="product-desc">' . $row["description"] . '</p>';
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