<?php
include "session.php";
?>

<html>
    <?php
    $title = 'Contact';
    include "styling.php";
    ?>
    <body>
        <?php
        include "topbar.php";
        ?>
        <p>The contact form is currently disabled.</p>
        <div class="contactform">
            <form action="/contact.php">
                <input type="text" placeholder="Your name" name="name"><br><br>
                <input type="text" placeholder="Your email" name="email"><br><br>
                <textarea rows="10" type="text" placeholder="" name="info">Any comments?</textarea><br><br>
                <button disabled type="submit">Submit</button>
            </form>
        </div>
    </body>
</html>