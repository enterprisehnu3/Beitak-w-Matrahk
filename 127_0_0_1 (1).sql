-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 01, 2026 at 11:14 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `beitak_db`
--
CREATE DATABASE IF NOT EXISTS `beitak_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `beitak_db`;

-- --------------------------------------------------------

--
-- Table structure for table `bookings`
--

CREATE TABLE `bookings` (
  `id` int(11) NOT NULL,
  `listing_id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `booking_date` datetime DEFAULT NULL,
  `check_in_date` datetime DEFAULT NULL,
  `total_price` float DEFAULT NULL,
  `commission_fee` float DEFAULT NULL,
  `cancelled_at` datetime DEFAULT NULL,
  `cancelled_by` varchar(20) DEFAULT NULL,
  `penalty_applied` float DEFAULT NULL,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `bookings`
--

INSERT INTO `bookings` (`id`, `listing_id`, `tenant_id`, `status`, `booking_date`, `check_in_date`, `total_price`, `commission_fee`, `cancelled_at`, `cancelled_by`, `penalty_applied`, `notes`) VALUES
(6, 3, 9, 'cancelled', '2026-04-20 13:15:05', NULL, 2500, 0, '2026-04-20 13:15:33', 'tenant', 0, NULL),
(9, 5, 10, 'confirmed', '2026-04-30 13:49:32', NULL, 4500, 360, NULL, NULL, 0, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `favorites`
--

CREATE TABLE `favorites` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `listing_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `listings`
--

CREATE TABLE `listings` (
  `id` int(11) NOT NULL,
  `owner_id` int(11) NOT NULL,
  `title` varchar(150) NOT NULL,
  `city` varchar(50) NOT NULL,
  `area` varchar(100) NOT NULL,
  `price` int(11) NOT NULL,
  `type` varchar(50) NOT NULL,
  `description` text NOT NULL,
  `rules` text DEFAULT NULL,
  `available_places` int(11) DEFAULT NULL,
  `gender_req` varchar(10) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `rental_period` varchar(20) DEFAULT NULL,
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `amenities` varchar(500) DEFAULT NULL,
  `views` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `listings`
--

INSERT INTO `listings` (`id`, `owner_id`, `title`, `city`, `area`, `price`, `type`, `description`, `rules`, `available_places`, `gender_req`, `is_active`, `created_at`, `rental_period`, `latitude`, `longitude`, `amenities`, `views`) VALUES
(3, 8, 'غرفة مفروشة ومريحة للطلاب', 'القاهرة', 'مدينة نصر', 2500, 'room', 'غرفة مكيفة شاملة الإنترنت والكهرباء في موقع مميز بمدينة نصر. مناسبة للطلبة لوجود هدوء تام للمذاكرة.', 'ممنوع التدخين، ممنوع اصطحاب الحيوانات الأليفة', 1, 'male', 1, '2026-04-19 19:37:21', 'monthly', NULL, NULL, NULL, 11),
(5, 8, 'غرفة فندقية بحمام خاص', 'Cairo', 'المعادي', 4500, 'room', '', 'غير مسموح بالتجمعات أو الحفلات للصوت العالي', 0, 'male', 1, '2026-04-19 19:37:21', 'monthly', NULL, NULL, 'wifi,ac,kitchen,parking', 8),
(7, 8, 'غرفة استضافة لفترة قصيرة', 'الإسكندرية', 'سموحة', 500, 'room', 'غرفة ممتازة للطلبة أو المغتربين لمدة قصيرة (الأسعار بالإسبوع)، قريبة من الجامعة والخدمات.', 'النظافة الشخصية ضرورة حتمية للمكان', 0, 'any', 1, '2026-04-19 19:37:21', 'weekly', NULL, NULL, NULL, 8);

-- --------------------------------------------------------

--
-- Table structure for table `listing_images`
--

CREATE TABLE `listing_images` (
  `id` int(11) NOT NULL,
  `listing_id` int(11) NOT NULL,
  `image_path` varchar(256) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `listing_images`
--

INSERT INTO `listing_images` (`id`, `listing_id`, `image_path`) VALUES
(15, 3, '/static/uploads/nasr.png'),
(17, 5, '/static/uploads/maadi.png'),
(19, 7, '/static/uploads/smouha.png');

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `content` text NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `sender_id`, `receiver_id`, `content`, `created_at`, `is_read`) VALUES
(1, 1, 9, 'احنا شوفنا الشكوى بتاعت حضرتك و هنحلها في خلال 24 ساعة كحد اقصى', '2026-04-20 12:32:16', 1),
(2, 9, 1, 'طب خد رقمي كلمني عليه  [رقم محجوب] ', '2026-04-20 12:32:41', 1),
(3, 9, 1, 'خد دا  [بريد محجوب] ', '2026-04-20 12:33:16', 1),
(4, 9, 1, '0112548459', '2026-04-20 12:33:29', 1),
(5, 9, 1, '010', '2026-04-20 12:33:36', 1),
(6, 9, 1, '60307841', '2026-04-20 12:33:45', 1),
(7, 9, 8, 'يا مش محترم', '2026-04-20 12:42:43', 1),
(8, 9, 8, 'يا ***', '2026-04-20 12:43:00', 1),
(9, 9, 8, 'يا علق', '2026-04-20 12:43:17', 1),
(10, 8, 9, '🤬', '2026-04-20 12:48:18', 1),
(11, 1, 9, 'طز فيك', '2026-04-20 12:53:51', 1),
(12, 1, 9, ' [رقم محجوب] ', '2026-04-20 12:53:57', 1),
(13, 1, 9, ' [بريد محجوب] ', '2026-04-20 12:54:14', 1),
(14, 1, 9, '@', '2026-04-20 12:54:19', 1),
(15, 11, 8, ' [رقم محجوب] ', '2026-04-20 17:33:40', 1),
(16, 11, 8, ' [بريد محجوب] ', '2026-04-20 17:33:52', 1);

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `title` varchar(100) NOT NULL,
  `message` text NOT NULL,
  `link` varchar(256) DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `title`, `message`, `link`, `is_read`, `created_at`) VALUES
(6, 9, 'تم قبول طلبك!', 'وافق المالك على حجزك وتأكد الدفع في غرفة فندقية بحمام خاص', '/dashboard', 1, '2026-04-20 11:49:18'),
(9, 9, 'تم قبول طلبك!', 'وافق المالك على حجزك وتأكد الدفع في غرفة استضافة لفترة قصيرة', '/dashboard', 1, '2026-04-20 12:47:15'),
(10, 9, 'تم قبول طلبك!', 'وافق المالك على حجزك وتأكد الدفع في شقة سكنية بالكامل لمشاركة الموظفين', '/dashboard', 1, '2026-04-20 12:47:23'),
(11, 10, 'تنبيه حول توثيق الحساب', 'عذراً، لم يتم قبول توثيق حسابك. السبب: الصورة جودتها وحشة برجاء اختيار صورة اخرى', '/reupload_id', 1, '2026-04-20 12:57:19'),
(13, 10, 'تم قبول طلبك!', 'وافق المالك على حجزك وتأكد الدفع في سرير في غرفة مشتركة بالقرب من المترو', '/dashboard', 1, '2026-04-20 13:13:18'),
(16, 11, 'تنبيه حول توثيق الحساب', 'عذراً، لم يتم قبول توثيق حسابك. السبب: الصورة مهزوزة برجاء اختيار صورة اخرى', '/reupload_id', 1, '2026-04-20 17:29:37'),
(17, 8, 'طلب حجز مدفوع جديد!', 'قام Ahmed بطلب حجز لـ شقة سكنية بالكامل لمشاركة الموظفين وتم سداد المبلغ!', '/dashboard', 1, '2026-04-20 17:37:38'),
(18, 8, 'طلب حجز مدفوع جديد!', 'قام عمرو محمد  بطلب حجز لـ غرفة فندقية بحمام خاص وتم سداد المبلغ!', '/dashboard', 1, '2026-04-30 13:50:26'),
(19, 10, 'تم قبول طلبك!', 'وافق المالك على حجزك وتأكد الدفع في غرفة فندقية بحمام خاص', '/dashboard', 0, '2026-04-30 13:52:40');

-- --------------------------------------------------------

--
-- Table structure for table `reviews`
--

CREATE TABLE `reviews` (
  `id` int(11) NOT NULL,
  `listing_id` int(11) NOT NULL,
  `author_id` int(11) NOT NULL,
  `rating` int(11) NOT NULL,
  `comment` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `support_tickets`
--

CREATE TABLE `support_tickets` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `subject` varchar(100) NOT NULL,
  `message` text NOT NULL,
  `admin_reply` text DEFAULT NULL,
  `admin_replied_at` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `support_tickets`
--

INSERT INTO `support_tickets` (`id`, `user_id`, `subject`, `message`, `admin_reply`, `admin_replied_at`, `status`, `created_at`) VALUES
(1, 9, 'other', 'لو سمحت انا لغيت الحجز و محدش خد مني غرامة ليه كدا', NULL, NULL, 'closed', '2026-04-20 12:27:17'),
(2, 9, 'payment_issue', '1', NULL, NULL, 'open', '2026-04-20 17:32:30');

-- --------------------------------------------------------

--
-- Table structure for table `transactions`
--

CREATE TABLE `transactions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `booking_id` int(11) DEFAULT NULL,
  `amount` float NOT NULL,
  `type` varchar(20) NOT NULL,
  `timestamp` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `transactions`
--

INSERT INTO `transactions` (`id`, `user_id`, `booking_id`, `amount`, `type`, `timestamp`) VALUES
(6, 9, 6, 2500, 'payment', '2026-04-20 13:15:19'),
(7, 9, 6, 2500, 'refund', '2026-04-20 13:15:33'),
(10, 10, 9, 4500, 'payment', '2026-04-30 13:50:26');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(64) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  `role` varchar(20) NOT NULL,
  `national_id_image` varchar(256) DEFAULT NULL,
  `is_verified` tinyint(1) DEFAULT NULL,
  `id_rejected` tinyint(1) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `smoker` tinyint(1) DEFAULT NULL,
  `sleep_schedule` varchar(20) DEFAULT NULL,
  `personality` varchar(20) DEFAULT NULL,
  `occupation` varchar(20) DEFAULT NULL,
  `reliability_score` int(11) DEFAULT NULL,
  `national_id_number` varchar(14) DEFAULT NULL,
  `wallet_balance` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `role`, `national_id_image`, `is_verified`, `id_rejected`, `gender`, `smoker`, `sleep_schedule`, `personality`, `occupation`, `reliability_score`, `national_id_number`, `wallet_balance`) VALUES
(1, 'admin', 'admin@beitak.com', 'scrypt:32768:8:1$kz4V4Q5VeCijPuQD$dd1199641137346f5e632b7f40de9fda53a0f2a6d3bd7936a78c462dcae76ed3c07c47e2b5fac9bd83c80947ac06f40fb16e74106c9f35b1d0a0dcb616817a16', 'admin', NULL, 1, 0, NULL, 0, NULL, NULL, NULL, 100, NULL, 0),
(8, 'Abubakr ', 'abubakr@beitak.com', 'scrypt:32768:8:1$UT4KPCEBspUJ8jaG$88ee185c01aa69a00152878eb3e114a0844d889dd2d3f5ed00b43fa7a9abe69b52d155c38245c22b308645f3af48d32fc5df68dc25db8a4a9094bbb6a14464d6', 'homeowner', '/static/uploads/ab99b743-4da6-4cb0-8031-46dde0f31a6a_png', 1, 0, 'male', 0, NULL, NULL, 'employee', 100, '11111111111111', 0),
(9, 'Ahmed', 'ahmed@beitak.com', 'scrypt:32768:8:1$CanAEvhOEJsHi7jx$40ac42e4a2a628a3898ef03e45db1f7963dcfcb1415be965970bd8175743f42a95acea9b4ac57c371c23b05e79bbd1f5bc86f8af7baff398c98b0b6c46a0bea5', 'student', '/static/uploads/80858476-32c1-4252-a441-c59111efc6f2_HNU_Ehab_ID.png', 1, 0, 'male', 0, NULL, NULL, NULL, 100, '22222222222222', 15000),
(10, 'عمرو محمد ', 'shtabwbkr@gmail.com', 'scrypt:32768:8:1$uMm7Md9Dlgl03jTx$4a4aa6f3a5e3ae39f5438e9bf7c7a798aa54bef802aaab4d7f687e0838458011f6a30024406ec22dadc7e26c87ba25b12871a33e9b6d6a5c961a7f66ecbc714e', 'student', 'REID_9c66bf41-32bd-4cd6-b2a8-d4ad30025b21.png', 1, 0, 'male', 0, NULL, NULL, NULL, 100, '30312051600378', 0),
(11, 'sss', 'sss@beitak.com', 'scrypt:32768:8:1$pkHcKjhHKINQc5NU$91e75cda1e2fbce3290766bc0099c9ecb76f0a5888069636e32f175810338ab46edad651a57cefa03df35b3ae235adace9e1096026917c086bc4ffb74fb0c704', 'homeowner', 'REID_7b61b290-bd9f-4949-9c18-292f42df5355.png', 1, 0, 'male', 0, NULL, NULL, NULL, 100, '23333333333333', 0);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `listing_id` (`listing_id`),
  ADD KEY `tenant_id` (`tenant_id`);

--
-- Indexes for table `favorites`
--
ALTER TABLE `favorites`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `listing_id` (`listing_id`);

--
-- Indexes for table `listings`
--
ALTER TABLE `listings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `owner_id` (`owner_id`);

--
-- Indexes for table `listing_images`
--
ALTER TABLE `listing_images`
  ADD PRIMARY KEY (`id`),
  ADD KEY `listing_id` (`listing_id`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sender_id` (`sender_id`),
  ADD KEY `receiver_id` (`receiver_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `reviews`
--
ALTER TABLE `reviews`
  ADD PRIMARY KEY (`id`),
  ADD KEY `listing_id` (`listing_id`),
  ADD KEY `author_id` (`author_id`);

--
-- Indexes for table `support_tickets`
--
ALTER TABLE `support_tickets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `transactions`
--
ALTER TABLE `transactions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `booking_id` (`booking_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `national_id_number` (`national_id_number`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bookings`
--
ALTER TABLE `bookings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `favorites`
--
ALTER TABLE `favorites`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `listings`
--
ALTER TABLE `listings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `listing_images`
--
ALTER TABLE `listing_images`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `reviews`
--
ALTER TABLE `reviews`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `support_tickets`
--
ALTER TABLE `support_tickets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `transactions`
--
ALTER TABLE `transactions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `bookings`
--
ALTER TABLE `bookings`
  ADD CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`listing_id`) REFERENCES `listings` (`id`),
  ADD CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`tenant_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `favorites`
--
ALTER TABLE `favorites`
  ADD CONSTRAINT `favorites_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `favorites_ibfk_2` FOREIGN KEY (`listing_id`) REFERENCES `listings` (`id`);

--
-- Constraints for table `listings`
--
ALTER TABLE `listings`
  ADD CONSTRAINT `listings_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `listing_images`
--
ALTER TABLE `listing_images`
  ADD CONSTRAINT `listing_images_ibfk_1` FOREIGN KEY (`listing_id`) REFERENCES `listings` (`id`);

--
-- Constraints for table `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `reviews`
--
ALTER TABLE `reviews`
  ADD CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`listing_id`) REFERENCES `listings` (`id`),
  ADD CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `support_tickets`
--
ALTER TABLE `support_tickets`
  ADD CONSTRAINT `support_tickets_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `transactions`
--
ALTER TABLE `transactions`
  ADD CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `transactions_ibfk_2` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
