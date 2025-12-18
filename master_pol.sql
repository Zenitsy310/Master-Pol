
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
CREATE DATABASE master_pol;

USE master_pol;
--

-- --------------------------------------------------------

--
-- Структура таблицы `employeecategories`
--

CREATE TABLE `employeecategories` (
  `CategoryID` int NOT NULL,
  `CategoryName` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `employees`
--

CREATE TABLE `employees` (
  `EmployeeID` int NOT NULL,
  `FullName` varchar(255) NOT NULL,
  `BirthDate` date DEFAULT NULL,
  `PassportData` text,
  `BankDetails` text,
  `HealthStatus` text,
  `CategoryID` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `employee_access`
--

CREATE TABLE `employee_access` (
  `AccessID` int NOT NULL,
  `EmployeeID` int NOT NULL,
  `EquipmentID` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `materials`
--

CREATE TABLE `materials` (
  `MaterialID` int NOT NULL,
  `Type` varchar(100) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `SupplierID` int DEFAULT NULL,
  `QuantityPerPackage` int DEFAULT NULL,
  `Unit` varchar(50) DEFAULT NULL,
  `Cost` decimal(10,2) DEFAULT NULL,
  `StockQuantity` int DEFAULT NULL,
  `MinStock` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `orderitems`
--

CREATE TABLE `orderitems` (
  `OrderItemID` int NOT NULL,
  `OrderID` int NOT NULL,
  `ProductID` int NOT NULL,
  `Quantity` int NOT NULL,
  `Price` decimal(10,2) NOT NULL,
  `ProductionDate` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `orders`
--

CREATE TABLE `orders` (
  `OrderID` int NOT NULL,
  `PartnerID` int NOT NULL,
  `EmployeeID` int DEFAULT NULL,
  `OrderDate` date NOT NULL,
  `Status` varchar(50) NOT NULL,
  `TotalAmount` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `partners`
--

CREATE TABLE `partners` (
  `PartnerID` int NOT NULL,
  `Type` varchar(50) NOT NULL,
  `CompanyName` varchar(255) DEFAULT NULL,
  `LegalAddress` text,
  `INN` varchar(20) DEFAULT NULL,
  `DirectorName` varchar(255) DEFAULT NULL,
  `Phone` varchar(50) DEFAULT NULL,
  `Email` varchar(255) DEFAULT NULL,
  `Logo` text,
  `Rating` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `products`
--

CREATE TABLE `products` (
  `ProductID` int NOT NULL,
  `Article` varchar(100) NOT NULL,
  `Type` varchar(100) DEFAULT NULL,
  `Name` varchar(255) NOT NULL,
  `Description` text,
  `MinPrice` decimal(10,2) DEFAULT NULL,
  `ProductionTime` int DEFAULT NULL,
  `CostPrice` decimal(10,2) DEFAULT NULL,
  `WorkshopNumber` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `saleshistory`
--

CREATE TABLE `saleshistory` (
  `SaleID` int NOT NULL,
  `PartnerID` int NOT NULL,
  `ProductID` int NOT NULL,
  `Quantity` int NOT NULL,
  `TotalAmount` decimal(10,2) NOT NULL,
  `SaleDate` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `employeecategories`
--
ALTER TABLE `employeecategories`
  ADD PRIMARY KEY (`CategoryID`);

--
-- Индексы таблицы `employees`
--
ALTER TABLE `employees`
  ADD PRIMARY KEY (`EmployeeID`),
  ADD KEY `idx_employees_category` (`CategoryID`);

--
-- Индексы таблицы `employee_access`
--
ALTER TABLE `employee_access`
  ADD PRIMARY KEY (`AccessID`),
  ADD KEY `EmployeeID` (`EmployeeID`);

--
-- Индексы таблицы `materials`
--
ALTER TABLE `materials`
  ADD PRIMARY KEY (`MaterialID`),
  ADD KEY `idx_materials_supplier` (`SupplierID`);

--
-- Индексы таблицы `orderitems`
--
ALTER TABLE `orderitems`
  ADD PRIMARY KEY (`OrderItemID`),
  ADD KEY `idx_orderitems_order` (`OrderID`),
  ADD KEY `idx_orderitems_product` (`ProductID`);

--
-- Индексы таблицы `orders`
--
ALTER TABLE `orders`
  ADD PRIMARY KEY (`OrderID`),
  ADD KEY `idx_orders_partner` (`PartnerID`),
  ADD KEY `idx_orders_employee` (`EmployeeID`),
  ADD KEY `idx_orders_date` (`OrderDate`);

--
-- Индексы таблицы `partners`
--
ALTER TABLE `partners`
  ADD PRIMARY KEY (`PartnerID`);

--
-- Индексы таблицы `products`
--
ALTER TABLE `products`
  ADD PRIMARY KEY (`ProductID`);

--
-- Индексы таблицы `saleshistory`
--
ALTER TABLE `saleshistory`
  ADD PRIMARY KEY (`SaleID`),
  ADD KEY `idx_saleshistory_partner` (`PartnerID`),
  ADD KEY `idx_saleshistory_product` (`ProductID`),
  ADD KEY `idx_saleshistory_date` (`SaleDate`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `employeecategories`
--
ALTER TABLE `employeecategories`
  MODIFY `CategoryID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `employees`
--
ALTER TABLE `employees`
  MODIFY `EmployeeID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `employee_access`
--
ALTER TABLE `employee_access`
  MODIFY `AccessID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `materials`
--
ALTER TABLE `materials`
  MODIFY `MaterialID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `orderitems`
--
ALTER TABLE `orderitems`
  MODIFY `OrderItemID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `orders`
--
ALTER TABLE `orders`
  MODIFY `OrderID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `partners`
--
ALTER TABLE `partners`
  MODIFY `PartnerID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `products`
--
ALTER TABLE `products`
  MODIFY `ProductID` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `saleshistory`
--
ALTER TABLE `saleshistory`
  MODIFY `SaleID` int NOT NULL AUTO_INCREMENT;

--
-- Ограничения внешнего ключа сохраненных таблиц
--

--
-- Ограничения внешнего ключа таблицы `employees`
--
ALTER TABLE `employees`
  ADD CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`CategoryID`) REFERENCES `employeecategories` (`CategoryID`);

--
-- Ограничения внешнего ключа таблицы `employee_access`
--
ALTER TABLE `employee_access`
  ADD CONSTRAINT `employee_access_ibfk_1` FOREIGN KEY (`EmployeeID`) REFERENCES `employees` (`EmployeeID`);

--
-- Ограничения внешнего ключа таблицы `materials`
--
ALTER TABLE `materials`
  ADD CONSTRAINT `materials_ibfk_1` FOREIGN KEY (`SupplierID`) REFERENCES `partners` (`PartnerID`);

--
-- Ограничения внешнего ключа таблицы `orderitems`
--
ALTER TABLE `orderitems`
  ADD CONSTRAINT `orderitems_ibfk_1` FOREIGN KEY (`OrderID`) REFERENCES `orders` (`OrderID`) ON DELETE CASCADE,
  ADD CONSTRAINT `orderitems_ibfk_2` FOREIGN KEY (`ProductID`) REFERENCES `products` (`ProductID`);

--
-- Ограничения внешнего ключа таблицы `orders`
--
ALTER TABLE `orders`
  ADD CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`PartnerID`) REFERENCES `partners` (`PartnerID`),
  ADD CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`EmployeeID`) REFERENCES `employees` (`EmployeeID`);

--
-- Ограничения внешнего ключа таблицы `saleshistory`
--
ALTER TABLE `saleshistory`
  ADD CONSTRAINT `saleshistory_ibfk_1` FOREIGN KEY (`PartnerID`) REFERENCES `partners` (`PartnerID`),
  ADD CONSTRAINT `saleshistory_ibfk_2` FOREIGN KEY (`ProductID`) REFERENCES `products` (`ProductID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

-- Заполнение базы данных тестовыми данными для производственной компании "Мастер пол"

USE master_pol;

-- Вставка данных в таблицу employeecategories
INSERT INTO employeecategories (CategoryID, CategoryName) VALUES
(1, 'Менеджер по продажам'),
(2, 'Производственный рабочий'),
(3, 'Мастер цеха'),
(4, 'Логист'),
(5, 'Бухгалтер');

-- Вставка данных в таблицу employeesч
INSERT INTO employees (EmployeeID, FullName, BirthDate, PassportData, BankDetails, HealthStatus, CategoryID) VALUES
(1, 'Иванов Сергей Петрович', '1985-03-15', '4510 123456, выдан ОВД Центрального р-на г. Москвы 15.03.2005', 'Сбербанк р/с 40817810012345678901', 'Здоров', 1),
(2, 'Петрова Анна Владимировна', '1990-07-22', '4511 654321, выдан ОВД Северного р-на г. Москвы 22.07.2010', 'ВТБ р/с 40817810098765432109', 'Здоров', 2),
(3, 'Сидоров Дмитрий Иванович', '1982-11-08', '4512 789012, выдан ОВД Западного р-на г. Москвы 08.11.2002', 'Альфа-Банк р/с 40817810045678901234', 'Здоров', 3),
(4, 'Козлова Елена Михайловна', '1988-05-30', '4513 345678, выдан ОВД Восточного р-на г. Москвы 30.05.2008', 'Тинькофф р/с 40817810056789012345', 'Здоров', 4),
(5, 'Николаев Алексей Викторович', '1979-12-14', '4514 901234, выдан ОВД Южного р-на г. Москвы 14.12.1999', 'Сбербанк р/с 40817810067890123456', 'Здоров', 5);

-- Вставка данных в таблицу partners
INSERT INTO partners (PartnerID, Type, CompanyName, LegalAddress, INN, DirectorName, Phone, Email, Logo, Rating) VALUES
(1, 'Поставщик', 'ООО "Древесные материалы"', 'г. Москва, ул. Промышленная, д. 15', '7701123456', 'Семенов А.В.', '+7 (495) 123-45-67', 'info@drevmaterial.ru', NULL, 5),
(2, 'Поставщик', 'ООО "ХимПромСнаб"', 'г. Москва, пр-т Ленинградский, д. 78', '7701987654', 'Кузнецова М.И.', '+7 (495) 234-56-78', 'sales@himprom.ru', NULL, 4),
(3, 'Клиент', 'ООО "СтройГрад"', 'г. Москва, ул. Строителей, д. 25', '7701654321', 'Васильев П.С.', '+7 (495) 345-67-89', 'zakaz@stroigrad.ru', NULL, 5),
(4, 'Клиент', 'ИП Романов К.Д.', 'г. Москва, ул. Центральная, д. 10', '7712345678', 'Романов К.Д.', '+7 (495) 456-78-90', 'romanov@mail.ru', NULL, 4),
(5, 'Поставщик', 'ООО "МеталлТрейд"', 'г. Москва, ш. Энтузиастов, д. 45', '7701765432', 'Орлов С.Н.', '+7 (495) 567-89-01', 'metal@metalltrade.ru', NULL, 3),
(6, 'Клиент', 'ООО "Евроремонт"', 'г. Москва, ул. Мира, д. 33', '7701876543', 'Соколова Т.В.', '+7 (495) 678-90-12', 'info@evroremont.ru', NULL, 5);

-- Вставка данных в таблицу products
INSERT INTO products (ProductID, Article, Type, Name, Description, MinPrice, ProductionTime, CostPrice, WorkshopNumber) VALUES
(1, 'LAM-001', 'Ламинат', 'Ламинат "Дуб классический"', 'Ламинат 32 класса, толщина 8мм, фаска по 4 сторонам', 850.00, 3, 450.00, 1),
(2, 'LAM-002', 'Ламинат', 'Ламинат "Бук натуральный"', 'Ламинат 33 класса, толщина 10мм, влагостойкий', 1200.00, 4, 650.00, 1),
(3, 'PARK-001', 'Паркет', 'Паркетная доска "Ясень"', 'Трехслойная паркетная доска, длина 2м, толщина 14мм', 2500.00, 5, 1200.00, 2),
(4, 'PARK-002', 'Паркет', 'Паркет "Дуб ручной работы"', 'Штучный паркет из массива дуба, толщина 16мм', 3800.00, 7, 1800.00, 2),
(5, 'LIN-001', 'Линолеум', 'Линолеум коммерческий', 'Коммерческий линолеум 4мм, класс износостойкости 34', 650.00, 2, 300.00, 3),
(6, 'LIN-002', 'Линолеум', 'Линолеум полукоммерческий', 'Полукоммерческий линолеум 3мм, антистатический', 480.00, 2, 220.00, 3),
(7, 'CARP-001', 'Ковролин', 'Ковролин офисный', 'Офисный ковролин с усиленной основой', 750.00, 3, 350.00, 4),
(8, 'CARP-002', 'Ковролин', 'Ковролин домашний', 'Мягкий ковролин для домашнего использования', 520.00, 3, 250.00, 4);

-- Вставка данных в таблицу materials
INSERT INTO materials (MaterialID, Type, Name, SupplierID, QuantityPerPackage, Unit, Cost, StockQuantity, MinStock) VALUES
(1, 'Древесина', 'Дубовая доска', 1, 10, 'шт', 3200.00, 150, 50),
(2, 'Древесина', 'Буковая доска', 1, 10, 'шт', 2800.00, 120, 40),
(3, 'Древесина', 'Ясеневая доска', 1, 10, 'шт', 3500.00, 80, 30),
(4, 'Химия', 'Лак для паркета', 2, 5, 'л', 450.00, 200, 100),
(5, 'Химия', 'Клей для ламината', 2, 10, 'кг', 280.00, 150, 75),
(6, 'Покрытие', 'ПВХ пленка', 2, 50, 'м²', 85.00, 1000, 500),
(7, 'Покрытие', 'Войлочная основа', 2, 100, 'м²', 45.00, 800, 400),
(8, 'Фурнитура', 'Металлический профиль', 5, 20, 'шт', 120.00, 300, 150),
(9, 'Фурнитура', 'Крепежные элементы', 5, 1000, 'шт', 0.85, 5000, 2000);

-- Вставка данных в таблицу orders
INSERT INTO orders (OrderID, PartnerID, EmployeeID, OrderDate, Status, TotalAmount) VALUES
(1, 3, 1, '2024-01-15', 'Выполнена', 185000.00),
(2, 4, 1, '2024-01-20', 'В производстве', 124500.00),
(3, 3, 1, '2024-02-05', 'Ожидает оплаты', 89000.00),
(4, 6, 1, '2024-02-10', 'Новая', 156000.00),
(5, 4, 1, '2024-02-12', 'В производстве', 67500.00),
(6, 6, 1, '2024-02-15', 'Новая', 234000.00);

-- Вставка данных в таблицу orderitems
INSERT INTO orderitems (OrderItemID, OrderID, ProductID, Quantity, Price, ProductionDate) VALUES
(1, 1, 1, 100, 850.00, '2024-01-18'),
(2, 1, 3, 40, 2500.00, '2024-01-18'),
(3, 2, 2, 60, 1200.00, '2024-02-05'),
(4, 2, 5, 80, 650.00, NULL),
(5, 3, 4, 15, 3800.00, '2024-02-08'),
(6, 3, 7, 40, 750.00, '2024-02-08'),
(7, 4, 1, 120, 850.00, NULL),
(8, 4, 6, 100, 480.00, NULL),
(9, 5, 8, 80, 520.00, '2024-02-18'),
(10, 5, 5, 30, 650.00, '2024-02-18'),
(11, 6, 3, 60, 2500.00, NULL),
(12, 6, 4, 20, 3800.00, NULL),
(13, 6, 2, 40, 1200.00, NULL);

-- Вставка данных в таблицу saleshistory
INSERT INTO saleshistory (SaleID, PartnerID, ProductID, Quantity, TotalAmount, SaleDate) VALUES
(1, 3, 1, 50, 42500.00, '2024-01-10'),
(2, 3, 3, 20, 50000.00, '2024-01-10'),
(3, 4, 2, 30, 36000.00, '2024-01-12'),
(4, 6, 5, 40, 26000.00, '2024-01-18'),
(5, 3, 4, 10, 38000.00, '2024-01-25'),
(6, 4, 7, 25, 18750.00, '2024-02-01'),
(7, 6, 1, 35, 29750.00, '2024-02-03'),
(8, 3, 2, 15, 18000.00, '2024-02-08');

-- Вставка данных в таблицу employee_access (пример оборудования)
INSERT INTO employee_access (AccessID, EmployeeID, EquipmentID) VALUES
(1, 1, 101),
(2, 1, 102),
(3, 2, 201),
(4, 2, 202),
(5, 3, 301),
(6, 3, 302),
(7, 4, 401),
(8, 5, 501);

-- Обновление автоинкрементных значений
ALTER TABLE employeecategories AUTO_INCREMENT = 6;
ALTER TABLE employees AUTO_INCREMENT = 6;
ALTER TABLE partners AUTO_INCREMENT = 7;
ALTER TABLE products AUTO_INCREMENT = 9;
ALTER TABLE materials AUTO_INCREMENT = 10;
ALTER TABLE orders AUTO_INCREMENT = 7;
ALTER TABLE orderitems AUTO_INCREMENT = 14;
ALTER TABLE saleshistory AUTO_INCREMENT = 9;
ALTER TABLE employee_access AUTO_INCREMENT = 9;

COMMIT;

-- Проверка вставленных данных
SELECT 'employeecategories' as Table_Name, COUNT(*) as Record_Count FROM employeecategories
UNION ALL
SELECT 'employees', COUNT(*) FROM employees
UNION ALL
SELECT 'partners', COUNT(*) FROM partners
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'materials', COUNT(*) FROM materials
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'orderitems', COUNT(*) FROM orderitems
UNION ALL
SELECT 'saleshistory', COUNT(*) FROM saleshistory
UNION ALL
SELECT 'employee_access', COUNT(*) FROM employee_access;
