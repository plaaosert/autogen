<html>
    <head>
        <title>Example page</title>
    </head>
    <body>
        <p>this is an example page</p>
        <p>flag: $$FLAG$$</p>
        <p>web base: $$BASE["WEB"]$$</p>
        <p>test_name: $$test_name$$</p>
        <p>test_password: $$test_password$$</p>
        <p>new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "mysql");</p>
        <p>$$BASE["SQL"]$$</p>
        <p>$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$</p>
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
                print "<pre>";
                print_r($row);
                print "</pre>";
            }
        } catch (Exception $e) {
            echo "sql failed";
            var_dump($e);
        }

        $conn->close();
        ?>
    </body>
</html>