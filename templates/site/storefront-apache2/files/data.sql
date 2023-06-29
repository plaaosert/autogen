CREATE DATABASE IF NOT EXISTS `storefront_data` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `storefront_data`;

CREATE TABLE `products` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `description` text NOT NULL,
  `price` REAL NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `products`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=0;

INSERT INTO `products` (`name`, `description`, `price`) VALUES
(# REPLACE HERE FOR PRODUCTS SQL);


CREATE TABLE `employee_logins` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `pass` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `employee_logins`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `employee_logins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

-- employee login insert

COMMIT;