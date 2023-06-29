<?php
include "session.php";

if (!isset($_SESSION["id"])) {
    header('Location: image_listing.php');
    exit();
}

if (!isset($_POST["caption"])) {
    header('Location: profile.php');
    exit();
}

//var_dump($_FILES);

$imageFileType = strtolower(pathinfo(basename($_FILES["file"]["name"]), PATHINFO_EXTENSION));

$caption = $_POST["caption"];
$filename = $_SESSION["id"] . time() . '.' . $imageFileType;

$target_dir = "/var/www/html/uploads/";
$target_file = $target_dir . $filename;
$uploadOk = 1;

//var_dump($imageFileType);

// Check if image file is a actual image or fake image
if(isset($_POST["submit"])) {
  $check = getimagesize($_FILES["file"]["tmp_name"]);
  if($check !== false) {
    $uploadOk = 1;
  } else {
    //echo "image size check failed";
    $uploadOk = 0;
  }
}

// Check if file already exists
if (file_exists($target_file)) {
  //echo "already exists";
  $uploadOk = 0;
}

// Check file size
if ($_FILES["file"]["size"] > 500000) {
  //echo "file too big";
  $uploadOk = 0;
}

// Allow certain file formats
if($imageFileType != "jpg" && $imageFileType != "png" && $imageFileType != "jpeg" && $imageFileType != "gif" ) {
  //echo "wrong extension";
  $uploadOk = 0;
}

// Check if $uploadOk is set to 0 by an error
if ($uploadOk != 0) {
  if (move_uploaded_file($_FILES["file"]["tmp_name"], $target_file)) {
      $uploadOk = 1;
  } else {
    $uploadOk = 0;
    //echo "move failed " . $target_file . "\n";
  }
}

// if uploadOk is still 1, we can go to the sql insertion part. if not, we redirect now
if ($uploadOk == 1) {
    $conn = new mysqli("$$BASE["SQL"]$$", "root", "$$SAVEDVARS_SQL["MYSQL_ROOT_PASSWORD"]$$", "imagesite_data");
    if ($conn->connect_error) {
        die("Failed to load page.");
    }

    try {
        $sql = "INSERT INTO posts (`author`, `caption`, `img_url`) VALUES (?, ?, ?);";
        $stmt = $conn->prepare($sql);

        $author_id = $_SESSION["id"];

        $imgurl = "uploads/" . $filename;
        $stmt->bind_param("iss", $author_id, $caption, $imgurl);

        $stmt->execute();

        if ($stmt->affected_rows > 0) {
            // post success
            header('Location: view_image.php?postid=' . $stmt->insert_id);
            exit();
        } else {
            header('Location: profile.php');
            exit();
        }

        $stmt->close();
    } catch (Exception $e) {
        header('Location: profile.php');
        exit();
    }

    $conn->close();
} else {
    header('Location: profile.php');
    exit();
}
?>