import sys
import re
import mysql.connector
import bcrypt
from math import ceil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit,
                             QSpinBox, QDoubleSpinBox, QFormLayout, QGroupBox,
                             QTabWidget, QMessageBox, QFrame, QSplitter, QDialog,
                             QSizePolicy, QToolButton, QMenu, QScrollArea)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap


class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()

    def get_partner_discount(self, partner_id):
        # В вашем SQL таблица называется saleshistory, а колонка PartnerID
        query = "SELECT SUM(TotalAmount) as total FROM saleshistory WHERE PartnerID = %s"
        res = self.execute_query(query, (partner_id,))

        # Переводим результат в число
        total = float(res[0]['total']) if res and res[0]['total'] else 0

        # Логика расчета из Приложения 1
        if total < 10000:
            return 0
        elif total < 50000:
            return 5
        elif total < 300000:
            return 10
        else:
            return 15

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host='127.0.0.1',
                port=3306,
                user='root',
                password='root',
                database='master_pol'
            )
            print("Успешное подключение к базе данных")
        except mysql.connector.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")

    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except mysql.connector.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []

    def execute_update(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return False


class PartnerDialog(QDialog):
    def __init__(self, db, partner_id=None):
        super().__init__()
        self.db = db
        self.partner_id = partner_id
        self.setWindowTitle("Партнёр / Поставщик")
        self.setFixedSize(500, 520)
        layout = QFormLayout(self)

        self.name = QLineEdit()
        self.type = QComboBox()
        self.type.addItems(["Покупатель", "Поставщик"])
        self.rating = QSpinBox()
        self.rating.setRange(0, 5)
        self.director = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.inn = QLineEdit()
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        self.error_label.hide()

        layout.addRow("Компания*", self.name)
        layout.addRow("Тип", self.type)
        layout.addRow("Рейтинг", self.rating)
        layout.addRow("Директор", self.director)
        layout.addRow("Телефон*", self.phone)
        layout.addRow("Email", self.email)
        layout.addRow("ИНН", self.inn)
        layout.addRow(self.error_label)

        save_btn = QPushButton("Сохранить")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save)
        layout.addRow(save_btn)

        if partner_id:
            self.load()

    def load(self):
        p = self.db.execute_query("SELECT * FROM partners WHERE PartnerID = %s", (self.partner_id,))
        if p:
            p = p[0]
            self.name.setText(p["CompanyName"])
            self.type.setCurrentText(p["Type"])
            self.rating.setValue(p["Rating"])
            self.director.setText(p["DirectorName"])
            self.phone.setText(p["Phone"])
            self.email.setText(p["Email"])
            self.inn.setText(p["INN"])

    def validate(self):
        self.error_label.hide()
        errors = []
        name = self.name.text().strip()
        phone = self.phone.text().strip()
        email = self.email.text().strip()

        if not name:
            errors.append("Укажите название компании")
        if not phone:
            errors.append("Укажите телефон")
        elif not re.match(r'^[\+]?[78]?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', phone):
            errors.append("Некорректный формат телефона")
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append("Некорректный email")

        if errors:
            self.error_label.setText(" • ".join(errors))
            self.error_label.show()
            return False
        return True

    def save(self):
        if not self.validate():
            return
        data = (
            self.name.text().strip(),
            self.type.currentText(),
            self.rating.value(),
            self.director.text().strip(),
            self.phone.text().strip(),
            self.email.text().strip() or None,
            self.inn.text().strip() or None
        )
        if self.partner_id:
            self.db.execute_update("""
                UPDATE partners SET
                    CompanyName = %s, Type = %s, Rating = %s,
                    DirectorName = %s, Phone = %s, Email = %s, INN = %s
                WHERE PartnerID = %s
            """, data + (self.partner_id,))
        else:
            self.db.execute_update("""
                INSERT INTO partners
                    (CompanyName, Type, Rating, DirectorName, Phone, Email, INN)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, data)
        self.accept()


class OrderDialog(QDialog):
    def __init__(self, db, order_id=None):
        super().__init__()
        self.db = db
        self.order_id = order_id
        self.setWindowTitle(f"{'Редактировать' if order_id else 'Добавить'} заявку")
        self.setFixedSize(600, 500)

        layout = QFormLayout(self)

        self.partner_combo = QComboBox()
        partners = self.db.execute_query("""
            SELECT PartnerID, CompanyName 
            FROM partners 
            WHERE TRIM(LOWER(Type)) = 'Клиент'
        """)
        for p in partners:
            self.partner_combo.addItem(p["CompanyName"], p["PartnerID"])
        layout.addRow("Партнёр*:", self.partner_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Новая", "В производстве", "Ожидает оплаты", "Выполнена", "Отменена"])
        layout.addRow("Статус:", self.status_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow("Дата:", self.date_edit)

        self.items_layout = QVBoxLayout()
        items_group = QGroupBox("Товары")
        items_group.setLayout(self.items_layout)
        layout.addRow(items_group)

        add_item_btn = QPushButton("Добавить товар")
        add_item_btn.clicked.connect(self.add_item_row)
        layout.addRow(add_item_btn)

        self.total_label = QLabel("Итого: 0 ₽")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #E74C3C;")
        layout.addRow(self.total_label)

        btns = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

        self.item_rows = []
        if order_id:
            self.load_order()
        else:
            self.add_item_row()

    def add_item_row(self):
        row = QHBoxLayout()
        product_combo = QComboBox()
        products = self.db.execute_query("SELECT ProductID, Name FROM products")
        for p in products:
            product_combo.addItem(p["Name"], p["ProductID"])

        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.1, 10000)
        qty_spin.setDecimals(2)
        qty_spin.setValue(1.0)
        qty_spin.setToolTip("Если введено дробное значение, будет округлено в большую сторону при сохранении")

        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 1000000)
        price_spin.setDecimals(2)
        price_spin.setReadOnly(True)  # 🔒 запрещаем ручной ввод
        price_spin.setValue(0)

        amount_label = QLabel("0.00 ₽")

        def update_amount():
            amount = qty_spin.value() * price_spin.value()
            amount_label.setText(f"{amount:.2f} ₽")
            self.update_total()

        qty_spin.valueChanged.connect(update_amount)
        price_spin.valueChanged.connect(update_amount)

        # Автоматическая подстановка цены при смене товара
        def on_product_change(index):
            product_id = product_combo.itemData(index)
            if product_id:
                price = self.get_product_price(product_id)
                price_spin.setValue(price)

        product_combo.currentIndexChanged.connect(on_product_change)

        row.addWidget(product_combo)
        row.addWidget(qty_spin)
        row.addWidget(price_spin)
        row.addWidget(amount_label)

        self.items_layout.addLayout(row)
        self.item_rows.append((product_combo, qty_spin, price_spin, amount_label))

    def get_product_price(self, product_id):
        rows = self.db.execute_query("SELECT MinPrice FROM products WHERE ProductID = %s", (product_id,))
        return rows[0]["MinPrice"] if rows else 0.0

    def update_total(self):
        total = sum(
            qty.value() * price.value()
            for _, qty, price, _ in self.item_rows
        )
        self.total_label.setText(f"Итого: {total:,.2f} ₽")

    def load_order(self):
        order = self.db.execute_query("SELECT * FROM orders WHERE OrderID = %s", (self.order_id,))[0]
        for i in range(self.partner_combo.count()):
            if self.partner_combo.itemData(i) == order["PartnerID"]:
                self.partner_combo.setCurrentIndex(i)
                break
        self.status_combo.setCurrentText(order["Status"])
        self.date_edit.setDate(QDate.fromString(str(order["OrderDate"]), "yyyy-MM-dd"))

        items = self.db.execute_query(
            "SELECT ProductID, Quantity, Price FROM orderitems WHERE OrderID = %s",
            (self.order_id,)
        )

        # Очистить текущие строки
        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.item_rows.clear()

        for item in items:
            self.add_item_row()
            combo, qty, price, _ = self.item_rows[-1]
            for i in range(combo.count()):
                if combo.itemData(i) == item["ProductID"]:
                    combo.setCurrentIndex(i)
                    break
            qty.setValue(item["Quantity"])
            price.setValue(item["Price"])

    def save(self):
        partner_id = self.partner_combo.currentData()
        status = self.status_combo.currentText()
        order_date = self.date_edit.date().toString("yyyy-MM-dd")

        if not partner_id:
            QMessageBox.warning(self, "Ошибка", "Выберите партнёра")
            return

        total = sum(qty.value() * price.value() for _, qty, price, _ in self.item_rows)
        if total == 0:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один товар с ценой")
            return

        if self.order_id:
            self.db.execute_update("""
                UPDATE orders SET PartnerID=%s, Status=%s, OrderDate=%s, TotalAmount=%s
                WHERE OrderID=%s
            """, (partner_id, status, order_date, total, self.order_id))
            self.db.execute_update("DELETE FROM orderitems WHERE OrderID=%s", (self.order_id,))
        else:
            self.db.execute_update("""
                INSERT INTO orders (PartnerID, Status, OrderDate, TotalAmount)
                VALUES (%s, %s, %s, %s)
            """, (partner_id, status, order_date, total))
            self.order_id = self.db.execute_query("SELECT LAST_INSERT_ID() as id")[0]["id"]

        for combo, qty, price, _ in self.item_rows:
            raw_qty = qty.value()
            final_qty = ceil(raw_qty)
            product_id = combo.currentData()
            unit_price = price.value()

            self.db.execute_update("""
                INSERT INTO orderitems (OrderID, ProductID, Quantity, Price)
                VALUES (%s, %s, %s, %s)
            """, (self.order_id, product_id, final_qty, unit_price))

        self.accept()


def style_table(table: QTableWidget):
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


class AuthDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setFixedSize(520, 620)
        self.setWindowTitle("Авторизация — Мастер пол")
        self.setStyleSheet("""
            QDialog { background-color: #F5F7FA; font-family: 'Segoe UI'; }
            QLabel { color: #2E3440; }
            QLineEdit {
                border: 1px solid #D1D5DB; border-radius: 8px; padding: 12px;
                background-color: #FFFFFF; font-size: 10pt;
            }
            QLineEdit:focus {
                border-color: #3B82F6; background-color: #EFF6FF;
            }
            QPushButton {
                padding: 12px 20px; border-radius: 8px; font-weight: bold;
                font-size: 10pt; min-height: 44px;
            }
            QPushButton.primary {
                background-color: #67BA80; color: white; border: none;
            }
            QPushButton.primary:hover { background-color: #5AA870; }
            QPushButton.text {
                background: transparent; color: #3B82F6; text-decoration: underline;
                border: none; font-weight: normal; padding: 4px;
            }
            QPushButton.text:hover { color: #2563EB; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(24)

        title = QLabel("Добро пожаловать в\n«Мастер пол»")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1F2937; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.login_form = self.create_login_form()
        self.stack.addWidget(self.login_form)

        self.register_form = self.create_register_form()
        self.stack.addWidget(self.register_form)

        self.notification = QLabel("")
        self.notification.setAlignment(Qt.AlignCenter)
        self.notification.hide()
        main_layout.addWidget(self.notification)

        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        self.switch_button = QPushButton()
        self.switch_button.setProperty("class", "text")
        self.switch_button.setCursor(Qt.PointingHandCursor)
        self.switch_button.clicked.connect(self.toggle_form)
        switch_layout.addWidget(self.switch_button)
        main_layout.addLayout(switch_layout)

        self.update_switch_text()

    def create_login_form(self):
        widget = QWidget()
        # Основной вертикальный макет
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        # Заголовок внутри формы
        title = QLabel("АВТОРИЗАЦИЯ")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #67BA80; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Поля ввода
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("👤 Логин")
        self.login_input.setMinimumHeight(40)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("🔒 Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)

        # Общий стиль для инпутов
        input_style = """
            QLineEdit {
                border: 2px solid #67BA80;
                border-radius: 10px;
                padding: 5px 10px;
                background-color: white;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 2px solid #559d6a;
                background-color: #FDFDFD;
            }
        """
        self.login_input.setStyleSheet(input_style)
        self.password_input.setStyleSheet(input_style)

        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)

        # Кнопка входа
        submit_btn = QPushButton("ВОЙТИ")
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setMinimumHeight(45)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #67BA80;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12pt;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #559d6a;
            }
        """)
        submit_btn.clicked.connect(self.login)
        layout.addWidget(submit_btn)

        return widget

    def create_register_form(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 20, 40, 30)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("РЕГИСТРАЦИЯ")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #67BA80; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Создание полей
        self.reg_fullname = QLineEdit()
        self.reg_fullname.setPlaceholderText("👤 Ваше полное имя (ФИО)")

        self.reg_login = QLineEdit()
        self.reg_login.setPlaceholderText("🔑 Придумайте логин")

        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("🔒 Пароль (минимум 6 символов)")
        self.reg_password.setEchoMode(QLineEdit.Password)

        # Применяем стиль и высоту ко всем полям сразу
        input_style = """
            QLineEdit {
                border: 2px solid #67BA80;
                border-radius: 10px;
                padding: 5px 10px;
                background-color: white;
                height: 35px;
            }
        """
        for field in [self.reg_fullname, self.reg_login, self.reg_password]:
            field.setStyleSheet(input_style)
            layout.addWidget(field)

        # Кнопка регистрации
        submit_btn = QPushButton("СОЗДАТЬ АККАУНТ")
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setMinimumHeight(45)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #67BA80;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 11pt;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #559d6a;
            }
        """)
        submit_btn.clicked.connect(self.register)
        layout.addWidget(submit_btn)

        return widget

    def toggle_form(self):
        self.stack.setCurrentIndex(1 - self.stack.currentIndex())
        self.clear_inputs()
        self.hide_notification()
        self.update_switch_text()

    def update_switch_text(self):
        if self.stack.currentIndex() == 0:
            self.switch_button.setText("Нет аккаунта? Зарегистрируйтесь")
        else:
            self.switch_button.setText("Уже есть аккаунт? Войдите")

    def clear_inputs(self):
        for w in [self.login_input, self.password_input, self.reg_login, self.reg_password, self.reg_fullname]:
            w.clear()

    def show_notification(self, text, success=True):
        self.notification.setText(text)
        self.notification.setStyleSheet(
            "background-color: #D1F0D9; color: #1F6B42;" if success else "background-color: #FAD1D1; color: #B02D2D;"
        )
        self.notification.show()
        QTimer.singleShot(4000, self.hide_notification)

    def hide_notification(self):
        self.notification.hide()

    def login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()
        if not login:
            self.show_notification("Логин не может быть пустым", False)
            return
        if not password:
            self.show_notification("Пароль не может быть пустым", False)
            return
        if len(login) < 3:
            self.show_notification("Логин должен содержать минимум 3 символа", False)
            return

        users = self.db.execute_query("SELECT * FROM users WHERE Login = %s", (login,))
        if not users:
            self.show_notification("Пользователь не найден", False)
            return

        user = users[0]
        if bcrypt.checkpw(password.encode('utf-8'), user['PasswordHash'].encode('utf-8')):
            self.show_notification("Успешный вход!")
            self.logged_in_user = user
            self.accept()
        else:

            self.show_notification("Неверный пароль", False)

    def register(self):
        login = self.reg_login.text().strip()
        password = self.reg_password.text()
        fullname = self.reg_fullname.text().strip()
        if not (login and password and fullname):
            self.show_notification("Все поля обязательны", False)
            return
        if len(password) < 6:
            self.show_notification("Пароль должен быть минимум 6 символов", False)
            return
        if self.db.execute_query("SELECT UserID FROM users WHERE Login = %s", (login,)):
            self.show_notification("Логин уже занят", False)
            return
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if self.db.execute_update(
                "INSERT INTO users (Login, PasswordHash, FullName) VALUES (%s, %s, %s)",
                (login, hashed, fullname)
        ):
            self.show_notification("Регистрация успешна! Войдите.", True)
            self.stack.setCurrentIndex(0)
            self.clear_inputs()
            self.update_switch_text()
        else:
            self.show_notification("Ошибка регистрации", False)


class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.db = DatabaseManager()

        # Настройка окна
        self.setWindowTitle("Мастер пол — Управление производством")
        self.setWindowIcon(QIcon("./res/Мастер пол.ico"))
        self.resize(1200, 900)

        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Вертикальный макет (Шапка + Нижняя часть)
        self.main_layout = QVBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы у края окна
        self.main_layout.setSpacing(0)

        # --- УНИКАЛЬНАЯ ШАПКА (Приложение 2) ---
        header_widget = QWidget()
        header_widget.setFixedHeight(70)
        header_widget.setStyleSheet("background-color: #FFFFFF; border-bottom: 2px solid #67BA80;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Логотип (Требование ТЗ: не искажать пропорции)
        logo_label = QLabel()
        logo_pixmap = QPixmap("./res/Мастер пол.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)

        # Заголовок в шапке
        title_label = QLabel("МАСТЕР ПОЛ")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-left: 10px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()  # Пружина

        # Имя пользователя
        user_label = QLabel(f"👤 {self.current_user.get('FullName', 'Сотрудник')}")
        user_label.setStyleSheet("color: #666; font-size: 10pt;")
        header_layout.addWidget(user_label)

        self.main_layout.addWidget(header_widget)

        # --- НИЖНЯЯ ЧАСТЬ (Сайдбар + Контент) ---
        # --- НИЖНЯЯ ЧАСТЬ (Контент слева, Сайдбар справа) ---
        self.body_layout = QHBoxLayout()
        self.main_layout.addLayout(self.body_layout)

        # СНАЧАЛА добавляем область контента
        self.create_content_area(self.body_layout)

        # ЗАТЕМ добавляем боковое меню
        self.create_sidebar(self.body_layout)
        self.setup_styles()

    def search_partners(self, text):
        """Функция живого поиска по таблице"""
        for i in range(self.partners_table.rowCount()):
            match = False
            for j in range(self.partners_table.columnCount()):
                item = self.partners_table.item(i, j)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.partners_table.setRowHidden(i, not match)

    def universal_search(self, text, table):
        """Универсальная фильтрация для любой таблицы"""
        for i in range(table.rowCount()):
            match = False
            for j in range(table.columnCount()):
                item = table.item(i, j)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            table.setRowHidden(i, not match)

    def create_header(self, layout):
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: white; border-bottom: 1px solid #67BA80;")
        header_frame.setFixedHeight(70)
        header_layout = QHBoxLayout(header_frame)


        # Логотип
        logo_label = QLabel()
        pixmap = QPixmap("./res/Мастер пол.png")
        if not pixmap.isNull():
            # scaled с KeepAspectRatio гарантирует отсутствие искажений (Приложение 2)
            logo_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)

        # Текстовый заголовок
        title = QLabel("МАСТЕР ПОЛ")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #000000; margin-left: 10px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Инфо о пользователе (из вашего функционала)
        user_info = QLabel(f"Пользователь: {self.current_user['FullName']}")
        user_info.setStyleSheet("color: #666666; font-size: 10pt;")
        header_layout.addWidget(user_info)

        layout.addWidget(header_frame)

    def setup_styles(self):
        self.setStyleSheet("""
            /* 1. Основной фон - Белый #FFFFFF */
            QMainWindow, QStackedWidget, QWidget#content_page {
                background-color: #FFFFFF;
            }

            /* 2. Дополнительный фон - Бежевый #F4E8D3 */
            /* Применяем ко ВСЕМ таблицам и их внутренним частям */
            QTableWidget {
                background-color: #F4E8D3;
                alternate-background-color: #F4E8D3;
                border: 1px solid #67BA80;
                gridline-color: #FFFFFF;
                font-family: 'Segoe UI';
            }

            /* Это закрашивает фон самих ячеек и пустую область таблицы */
            QTableWidget::item { background-color: #F4E8D3; }
            QTableWidget::viewport { background-color: #F4E8D3; }

            /* Поля ввода и выпадающие списки */
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
                background-color: #F4E8D3;
                border: 1px solid #67BA80;
                border-radius: 3px;
                padding: 5px;
            }

            /* 3. Акцентирование - Зеленый #67BA80 */
            /* Заголовки таблиц */
            QHeaderView::section {
                background-color: #67BA80;
                color: #FFFFFF;
                font-weight: bold;
                border: 1px solid #FFFFFF;
                padding: 5px;
            }

            /* Кнопки целевого действия */
            /* Глобальный стиль кнопок — только зеленый и белый */
            QPushButton {
                background-color: #67BA80;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Segoe UI';
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #559d6a;
            }

            /* Если есть второстепенные кнопки, их можно сделать бежевыми с зеленой рамкой */
            QPushButton#secondary {
                background-color: #F4E8D3;
                color: #333333;
                border: 1px solid #67BA80;
            }

            /* Боковая панель */
            QFrame#sidebar_frame {
                background-color: #F4E8D3;
                border-right: 2px solid #67BA80;
            }
        """)

    def create_sidebar(self, main_layout):
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setProperty("class", "sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo_container = QWidget()
        logo_container.setFixedHeight(80)
        logo_container.setStyleSheet("background-color: #1A252F; border-bottom: 1px solid #34495E;")
        logo_layout = QVBoxLayout(logo_container)
        logo_label = QLabel("МАСТЕР ПОЛ")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("color: #67BA80; font-size: 18px; font-weight: bold; padding: 20px 0;")
        logo_layout.addWidget(logo_label)
        sidebar_layout.addWidget(logo_container)

        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 20, 0, 20)
        nav_layout.setSpacing(2)

        nav_buttons = [
            ("Главная панель", self.show_main),
            ("Партнеры", self.show_partners),
            ("Продукция", self.show_products),
            ("Производство", self.show_production),
            ("Заявки", self.show_orders),
            ("Сотрудники", self.show_employees),
            ("Материалы", self.show_materials),
            ("Склад", self.show_warehouse),
            ("Поставщики", self.show_suppliers),
            ("Аналитика", self.show_analytics)
        ]
        self.nav_buttons = []
        for text, callback in nav_buttons:
            btn = QPushButton(text)
            btn.setProperty("class", "sidebar-button")
            btn.clicked.connect(callback)
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)
        nav_layout.addStretch()

        exit_btn = QPushButton("Выход")
        exit_btn.setProperty("class", "sidebar-button")
        exit_btn.setStyleSheet("color: #E74C3C;")
        exit_btn.clicked.connect(self.logout)
        nav_layout.addWidget(exit_btn)

        sidebar_layout.addWidget(nav_container)
        main_layout.addWidget(sidebar)

    def logout(self):
        self.close()
        auth = AuthDialog(self.db)
        if auth.exec_() == QDialog.Accepted:
            win = MainWindow(auth.logged_in_user)
            win.show()
            QApplication.activeWindow().close()

    def create_content_area(self, main_layout):
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #F5F7FA;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E4E7ED;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)
        self.title_label = QLabel("Главная панель")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #303133;")
        user_name = QLabel(self.current_user['FullName'])
        user_name.setStyleSheet("color: #606266; margin-right: 15px;")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(user_name)
        content_layout.addWidget(top_bar)

        content_container = QWidget()
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(30, 30, 30, 30)
        self.stacked_widget = QStackedWidget()
        content_container_layout.addWidget(self.stacked_widget)
        content_layout.addWidget(content_container)

        self.create_main_screen()
        self.create_partners_screen()
        self.create_products_screen()
        self.create_orders_screen()
        self.create_employees_screen()
        self.create_materials_screen()
        self.create_suppliers_screen()
        self.create_analytics_screen()

        main_layout.addWidget(content_widget)

    def create_main_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(15)

        partners_count = self.db.execute_query("SELECT COUNT(*) as count FROM partners")[0]['count']
        active_orders = self.db.execute_query("SELECT COUNT(*) as count FROM orders WHERE Status != 'Выполнена'")[0][
            'count']
        products_count = self.db.execute_query("SELECT COUNT(*) as count FROM products")[0]['count']
        low_stock = self.db.execute_query("SELECT COUNT(*) as count FROM materials WHERE StockQuantity < MinStock")[0][
            'count']

        for title, value, trend in [
            ("Активные партнеры", str(partners_count), "+12%"),
            ("Заявки в работе", str(active_orders), "+5%"),
            ("Виды продукции", str(products_count), "+3%"),
            ("Материалы с низким запасом", str(low_stock), "Требуют заказа")
        ]:
            card = QWidget()
            card.setStyleSheet(
                "background-color: #FFFFFF; border: 1px solid #E4E7ED; border-radius: 8px; padding: 20px;")
            card.setFixedHeight(120)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(20, 20, 20, 20)
            v = QLabel(value)
            v.setStyleSheet("font-size: 28px; font-weight: bold; color: #303133;")
            t = QLabel(title)
            t.setStyleSheet("font-size: 14px; color: #909399; margin-top: 8px;")
            cl.addWidget(v)
            cl.addWidget(t)
            if trend:
                tr = QLabel(trend)
                tr.setStyleSheet("color: #67BA80; font-size: 12px; margin-top: 5px;")
                cl.addWidget(tr)
            stats_layout.addWidget(card)
        layout.addWidget(stats_widget)

        columns_widget = QWidget()
        columns_layout = QHBoxLayout(columns_widget)
        columns_layout.setSpacing(20)

        orders_group = QGroupBox("Последние заявки")
        orders_layout = QVBoxLayout(orders_group)
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Партнер", "Статус", "Сумма", "Дата"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        orders = self.db.execute_query("""
            SELECT o.OrderID, p.CompanyName, o.Status, o.TotalAmount, o.OrderDate 
            FROM orders o LEFT JOIN partners p ON o.PartnerID = p.PartnerID 
            ORDER BY o.OrderDate DESC LIMIT 10
        """)
        table.setRowCount(len(orders))
        for i, o in enumerate(orders):
            table.setItem(i, 0, QTableWidgetItem(str(o['OrderID'])))
            table.setItem(i, 1, QTableWidgetItem(o['CompanyName']))
            table.setItem(i, 2, QTableWidgetItem(o['Status']))
            table.setItem(i, 3, QTableWidgetItem(f"{o['TotalAmount']:,.0f} ₽"))
            table.setItem(i, 4, QTableWidgetItem(str(o['OrderDate'])))
        orders_layout.addWidget(table)

        activity_group = QGroupBox("Последняя активность")
        activity_layout = QVBoxLayout(activity_group)
        recent_sales = self.db.execute_query("""
            SELECT p.CompanyName, SUM(s.Quantity) as quantity 
            FROM saleshistory s LEFT JOIN partners p ON s.PartnerID = p.PartnerID 
            GROUP BY p.CompanyName ORDER BY quantity DESC LIMIT 5
        """)
        for sale in recent_sales:
            label = QLabel(f"• {sale['CompanyName']}: {sale['quantity']} ед.")
            label.setStyleSheet("padding: 8px 0; color: #606266; border-bottom: 1px solid #EBEEF5;")
            activity_layout.addWidget(label)

        columns_layout.addWidget(orders_group, 2)
        columns_layout.addWidget(activity_group, 1)
        layout.addWidget(columns_widget)

        self.stacked_widget.addWidget(widget)

    def create_partners_screen(self):
        widget = QWidget()
        # Основной фон окна — белый (#FFFFFF)
        widget.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- ЗАГОЛОВОК СЕКЦИИ (Для уникальности) ---
        page_title = QLabel("Управление базой партнеров")
        page_title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #333; margin-bottom: 5px;")
        layout.addWidget(page_title)

        # Панель управления
        control_panel = QHBoxLayout()

        # Стилизованный поиск
        self.partner_search = QLineEdit()
        self.partner_search.setPlaceholderText("🔍 Поиск по названию или директору...")
        self.partner_search.setFixedHeight(40)
        self.partner_search.setMinimumWidth(400)
        # Рамка цвета #67BA80 (ТЗ)
        self.partner_search.setStyleSheet("""
            QLineEdit {
                border: 2px solid #67BA80; 
                border-radius: 20px; 
                padding-left: 15px; 
                background-color: #FDFDFD;
            }
        """)
        # В методе create_partners_screen
        self.partner_search.textChanged.connect(lambda text: self.universal_search(text, self.partners_table))
        control_panel.addWidget(self.partner_search)

        control_panel.addStretch()

        # Кнопка добавления (Цвет #67BA80 по ТЗ)
        add_btn = QPushButton("+ НОВЫЙ ПАРТНЕР")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedWidth(200)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #67BA80;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 10pt;
                height: 40px;
            }
            QPushButton:hover {
                background-color: #559d6a;
            }
        """)
        add_btn.clicked.connect(self.add_partner)
        control_panel.addWidget(add_btn)

        layout.addLayout(control_panel)

        # --- ТАБЛИЦА (Цвета по ТЗ) ---
        self.partners_table = QTableWidget()
        # Используем дополнительный фон #F4E8D3 для таблицы
        self.partners_table.setStyleSheet("""
            QTableWidget {
                background-color: #F4E8D3; 
                border: 1px solid #67BA80;
                gridline-color: #FFFFFF;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #67BA80;
                color: white;
                font-weight: bold;
                border: none;
                height: 45px;
            }
        """)

        self.partners_table.setColumnCount(7)
        self.partners_table.setHorizontalHeaderLabels([
            "ID", "Компания", "Тип", "Рейтинг", "Телефон", "Скидка %", "Действия"
        ])
        self.partners_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.partners_table.verticalHeader().setVisible(False)  # Убираем номера строк для чистоты

        layout.addWidget(self.partners_table)

        self.load_partners_data()
        self.stacked_widget.addWidget(widget)

    def load_partners_data(self):
        try:
            self.partners_table.setColumnCount(6)
            self.partners_table.setHorizontalHeaderLabels([
                "Тип", "Наименование", "Директор", "Телефон", "Рейтинг", "Скидка (%)"
            ])

            # ИСПРАВЛЕННЫЙ ЗАПРОС (без JOIN, так как тип уже в таблице partners)
            query = """
                SELECT PartnerID as id, Type as type, CompanyName as company_name, 
                       DirectorName as director_name, Phone as phone, Rating as rating 
                FROM partners
            """
            partners = self.db.execute_query(query)

            if not partners:
                print("Данные не найдены")
                return

            self.partners_table.setRowCount(len(partners))

            for i, p in enumerate(partners):
                self.partners_table.setItem(i, 0, QTableWidgetItem(str(p.get('type', ''))))
                self.partners_table.setItem(i, 1, QTableWidgetItem(str(p.get('company_name', ''))))
                self.partners_table.setItem(i, 2, QTableWidgetItem(str(p.get('director_name', ''))))
                self.partners_table.setItem(i, 3, QTableWidgetItem(str(p.get('phone', ''))))
                self.partners_table.setItem(i, 4, QTableWidgetItem(str(p.get('rating', '0'))))

                # Скидка теперь будет считаться из таблицы saleshistory
                discount = self.db.get_partner_discount(p.get('id'))
                self.partners_table.setItem(i, 5, QTableWidgetItem(f"{discount}%"))

            self.partners_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        except Exception as e:
            print(f"Ошибка: {e}")
    def add_partner(self):
        d = PartnerDialog(self.db)
        if d.exec_():
            self.load_partners_data()

    def edit_partner(self, pid):
        d = PartnerDialog(self.db, pid)
        if d.exec_():
            self.load_partners_data()

    def show_get_partner_discount(self, partner_id, partner_name):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"История продаж — {partner_name}")
        dialog.resize(800, 500)
        layout = QVBoxLayout(dialog)

        label = QLabel(f"История реализации продукции партнером: <b>{partner_name}</b>")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        # Используем orders + orderitems, если нет saleshistory
        sales = self.db.execute_query("""
            SELECT o.OrderDate as SaleDate, pr.Name as ProductName, oi.Quantity, (oi.Quantity * oi.Price) as TotalAmount
            FROM orders o
            JOIN orderitems oi ON o.OrderID = oi.OrderID
            JOIN products pr ON oi.ProductID = pr.ProductID
            WHERE o.PartnerID = %s
            ORDER BY o.OrderDate DESC
        """, (partner_id,))

        table = QTableWidget(len(sales), 4)
        table.setHorizontalHeaderLabels(["Дата", "Продукция", "Количество", "Сумма"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

        for i, s in enumerate(sales):
            table.setItem(i, 0, QTableWidgetItem(str(s["SaleDate"])))
            table.setItem(i, 1, QTableWidgetItem(s["ProductName"]))
            table.setItem(i, 2, QTableWidgetItem(str(s["Quantity"])))
            table.setItem(i, 3, QTableWidgetItem(f"{s['TotalAmount']:,.0f} ₽"))

        layout.addWidget(table)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def search_partners(self):
        self.load_partners_data()

    def create_products_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        tabs = QTabWidget()

        catalog_tab = QWidget()
        catalog_layout = QVBoxLayout(catalog_tab)
        catalog_layout.setSpacing(15)

        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)

        # 1. Сначала СОЗДАЕМ объекты
        self.product_type_combo = QComboBox()
        self.product_type_combo.addItems(["Все типы", "Ламинат", "Паркет", "Линолеум", "Ковролин"])

        self.product_search = QLineEdit()  # ЭТОЙ СТРОКИ НЕ ХВАТАЛО!

        # 2. Теперь НАСТРАИВАЕМ их
        self.product_search.setPlaceholderText("🔍 Поиск продукции...")

        # 3. Добавляем в макет
        filter_layout.addWidget(QLabel("Тип:"))
        filter_layout.addWidget(self.product_type_combo)
        filter_layout.addWidget(self.product_search)
        filter_layout.addStretch()

        catalog_layout.addWidget(filter_widget)

        # 4. Создаем таблицу (ВАЖНО: создаем ДО подключения поиска)
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "Артикул", "Наименование", "Тип", "Минимальная цена", "Время производства", "Себестоимость"
        ])

        # 5. Теперь подключаем поиск (когда и поиск, и таблица уже существуют)
        self.product_search.textChanged.connect(lambda text: self.universal_search(text, self.products_table))
        self.product_type_combo.currentTextChanged.connect(
            lambda text: self.universal_search(text if text != "Все типы" else "", self.products_table))

        self.load_products_data()
        catalog_layout.addWidget(self.products_table)
        tabs.addTab(catalog_tab, "Каталог продукции")
        layout.addWidget(tabs)
        self.stacked_widget.addWidget(widget)

    def load_products_data(self):
        products = self.db.execute_query("SELECT * FROM products")
        self.products_table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.products_table.setItem(i, 0, QTableWidgetItem(p['Article']))
            self.products_table.setItem(i, 1, QTableWidgetItem(p['Name']))
            self.products_table.setItem(i, 2, QTableWidgetItem(p['Type']))
            price_item = QTableWidgetItem(f"{p['MinPrice']:,.0f} ₽")
            price_item.setForeground(QColor("#67BA80"))
            self.products_table.setItem(i, 3, price_item)
            self.products_table.setItem(i, 4, QTableWidgetItem(f"{p['ProductionTime']} дней"))
            self.products_table.setItem(i, 5, QTableWidgetItem(f"{p['CostPrice']:,.0f} ₽"))

    def create_orders_screen(self):
        widget = QWidget()
        widget.setObjectName("content_page")
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 1. ВЕРХНЯЯ ПАНЕЛЬ
        top_panel_widget = QWidget()
        top_panel = QHBoxLayout(top_panel_widget)

        self.order_search = QLineEdit()
        self.order_search.setPlaceholderText("🔍 Поиск по номеру или партнёру...")
        self.order_search.textChanged.connect(lambda text: self.universal_search(text, self.orders_table))
        top_panel.addWidget(self.order_search)

        top_panel.addStretch()

        add_btn = QPushButton("+ ДОБАВИТЬ ЗАЯВКУ")
        add_btn.clicked.connect(self.add_order)
        top_panel.addWidget(add_btn)

        main_layout.addWidget(top_panel_widget)

        # --- РАЗДЕЛИТЕЛЬ (Splitter) ---
        self.splitter = QSplitter(Qt.Vertical)

        # 2. ТАБЛИЦА ЗАЯВОК (Верхняя часть)
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(4)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Партнёр", "Статус", "Сумма"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # КРИТИЧЕСКИ ВАЖНАЯ СТРОКА: подключаем обновление деталей при клике
        self.orders_table.itemSelectionChanged.connect(self.show_order_details)

        self.orders_table.setMinimumHeight(250)
        self.splitter.addWidget(self.orders_table)

        # 3. ОБЕРТКА ДЛЯ ДЕТАЛЕЙ (Нижняя часть) со СКРОЛЛЕРОМ
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.order_details_widget = QWidget()
        self.order_details_widget.setObjectName("details_area")
        # Устанавливаем белый фон области деталей
        self.order_details_widget.setStyleSheet("background-color: #FFFFFF;")
        self.order_details_layout = QVBoxLayout(self.order_details_widget)
        self.order_details_layout.setContentsMargins(15, 15, 15, 15)

        welcome = QLabel("Выберите заявку в таблице выше для просмотра деталей")
        welcome.setStyleSheet("color: #67BA80; font-weight: bold;")
        welcome.setAlignment(Qt.AlignCenter)
        self.order_details_layout.addWidget(welcome)

        scroll_area.setWidget(self.order_details_widget)
        self.splitter.addWidget(scroll_area)

        self.splitter.setSizes([400, 300])
        main_layout.addWidget(self.splitter)
        self.stacked_widget.addWidget(widget)

    def load_orders_data(self):
        self.search_orders()

    def search_orders(self):
        search = self.order_search.text().strip()
        if search:
            orders = self.db.execute_query("""
                SELECT o.OrderID, p.CompanyName, o.Status, o.TotalAmount
                FROM orders o
                LEFT JOIN partners p ON o.PartnerID = p.PartnerID
                WHERE o.OrderID LIKE %s OR p.CompanyName LIKE %s
                ORDER BY o.OrderDate DESC
            """, (f"%{search}%", f"%{search}%"))
        else:
            orders = self.db.execute_query("""
                SELECT o.OrderID, p.CompanyName, o.Status, o.TotalAmount
                FROM orders o
                LEFT JOIN partners p ON o.PartnerID = p.PartnerID
                ORDER BY o.OrderDate DESC
            """)
        self.orders_table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            self.orders_table.setItem(r, 0, QTableWidgetItem(str(o["OrderID"])))
            self.orders_table.setItem(r, 1, QTableWidgetItem(o["CompanyName"] or "—"))
            self.orders_table.setItem(r, 2, QTableWidgetItem(o["Status"]))
            self.orders_table.setItem(r, 3, QTableWidgetItem(f'{o["TotalAmount"]:,.0f} ₽'))

    def show_order_details(self):
        # 1. Полная очистка предыдущего содержимого
        while self.order_details_layout.count():
            item = self.order_details_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                # Рекурсивно удаляем вложенные макеты (например, кнопки)
                while item.layout().count():
                    child = item.layout().takeAt(0).widget()
                    if child: child.deleteLater()

        row = self.orders_table.currentRow()
        if row < 0:
            welcome = QLabel("Выберите заявку для просмотра деталей")
            welcome.setStyleSheet("color: #909399; font-style: italic;")
            self.order_details_layout.addWidget(welcome)
            return

        try:
            order_id = int(self.orders_table.item(row, 0).text())
        except (AttributeError, ValueError):
            return

        # 2. Получение данных из БД
        order_data = self.db.execute_query("""
            SELECT o.*, p.CompanyName, p.Phone, p.Email, p.PartnerID
            FROM orders o
            JOIN partners p ON p.PartnerID = o.PartnerID
            WHERE o.OrderID = %s
        """, (order_id,))

        if not order_data: return
        order = order_data[0]

        # 3. Кнопки управления (Зеленые/Бежевые по ТЗ)
        btns = QHBoxLayout()
        edit_btn = QPushButton("✎ Редактировать")
        # Используем класс secondary для бежевой кнопки или оставляем стандартную зеленую
        edit_btn.clicked.connect(lambda: self.edit_order(order_id))

        history_btn = QPushButton("История партнёра")
        history_btn.clicked.connect(lambda: self.show_partner_sales_history(order["PartnerID"], order["CompanyName"]))

        btns.addWidget(edit_btn)
        btns.addWidget(history_btn)
        btns.addStretch()
        self.order_details_layout.addLayout(btns)

        # 4. Основная информация (Форма)
        box = QGroupBox(f"Информация о заказе №{order_id}")
        box.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #67BA80; border: 1px solid #67BA80; margin-top: 10px; padding-top: 10px; }")
        f = QFormLayout(box)
        f.setLabelAlignment(Qt.AlignRight)

        f.addRow("Партнёр:", QLabel(str(order["CompanyName"])))
        f.addRow("Контакты:", QLabel(f'{order["Phone"] or "—"} | {order["Email"] or "—"}'))
        f.addRow("Статус:", QLabel(str(order["Status"])))
        f.addRow("Сумма заказа:", QLabel(f'<b>{order["TotalAmount"]:,.2f} ₽</b>'))
        f.addRow("Дата создания:", QLabel(str(order["OrderDate"])))

        self.order_details_layout.addWidget(box)

        # 5. Таблица состава заказа (ДП)
        items = self.db.execute_query("""
            SELECT pr.Name, oi.Quantity, oi.Price
            FROM orderitems oi
            JOIN products pr ON pr.ProductID = oi.ProductID
            WHERE oi.OrderID = %s
        """, (order_id,))

        if items:
            lbl_items = QLabel("Состав заказа:")
            lbl_items.setStyleSheet("font-weight: bold; margin-top: 10px;")
            self.order_details_layout.addWidget(lbl_items)

            table = QTableWidget(len(items), 4)
            table.setHorizontalHeaderLabels(["Продукт", "Кол-во", "Цена", "Сумма"])
            # Заставляем таблицу продуктов занимать всё место и быть бежевой
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setMinimumHeight(150)

            for i, it in enumerate(items):
                table.setItem(i, 0, QTableWidgetItem(it["Name"]))
                table.setItem(i, 1, QTableWidgetItem(str(it["Quantity"])))
                table.setItem(i, 2, QTableWidgetItem(f'{it["Price"]:,.2f} ₽'))
                total = it["Quantity"] * it["Price"]
                table.setItem(i, 3, QTableWidgetItem(f'{total:,.2f} ₽'))

            self.order_details_layout.addWidget(table)

        # Распорка в конце, чтобы элементы не расползались по высоте
        self.order_details_layout.addStretch()

    def add_order(self):
        dialog = OrderDialog(self.db)
        if dialog.exec_():
            self.load_orders_data()

    def edit_order(self, order_id):
        dialog = OrderDialog(self.db, order_id)
        if dialog.exec_():
            self.load_orders_data()

    def create_employees_screen(self):
        widget = QWidget()
        widget.setObjectName("content_page")  # Привязка к белому фону из setup_styles
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("СПИСОК СОТРУДНИКОВ")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # ПОИСК
        self.emp_search = QLineEdit()
        self.emp_search.setPlaceholderText("🔍 Поиск по ФИО, должности или категории...")
        # Подключаем наш универсальный поиск к этой таблице
        self.emp_search.textChanged.connect(lambda text: self.universal_search(text, self.employees_table))
        layout.addWidget(self.emp_search)

        # ТАБЛИЦА
        self.employees_table = QTableWidget()
        # Убираем внутренние стили таблицы здесь, чтобы работал глобальный setup_styles
        self.employees_table.setColumnCount(6)
        self.employees_table.setHorizontalHeaderLabels(
            ["ФИО", "Должность", "Дата рождения", "Контакты", "Здоровье", "Категория"])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.employees_table.verticalHeader().setVisible(False) # Скрываем номера строк для красоты

        # Загрузка данных
        try:
            employees = self.db.execute_query(
                "SELECT e.*, c.CategoryName FROM employees e LEFT JOIN employeecategories c ON e.CategoryID = c.CategoryID")
            self.employees_table.setRowCount(len(employees))
            for i, e in enumerate(employees):
                self.employees_table.setItem(i, 0, QTableWidgetItem(str(e.get('FullName', ''))))
                self.employees_table.setItem(i, 1, QTableWidgetItem(str(e.get('CategoryName', ''))))
                self.employees_table.setItem(i, 2, QTableWidgetItem(str(e.get('BirthDate', ''))))
                self.employees_table.setItem(i, 3, QTableWidgetItem("Показать контакты"))
                self.employees_table.setItem(i, 4, QTableWidgetItem(str(e.get('HealthStatus', ''))))
                self.employees_table.setItem(i, 5, QTableWidgetItem(str(e.get('CategoryName', ''))))
        except Exception as ex:
            print(f"Ошибка загрузки сотрудников: {ex}")

        layout.addWidget(self.employees_table)
        self.stacked_widget.addWidget(widget)
    def create_materials_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        tabs = QTabWidget()

        materials_tab = QWidget()
        materials_layout = QVBoxLayout(materials_tab)
        materials_layout.setSpacing(15)

        control_panel = QHBoxLayout()
        self.material_search = QLineEdit()  # Проверьте наличие этой строки
        self.material_search.setPlaceholderText("🔍 Поиск материалов...")
        self.material_search.textChanged.connect(lambda text: self.universal_search(text, self.materials_table))
        self.material_search.setMinimumWidth(300)
        control_panel.addWidget(self.material_search)
        control_panel.addStretch()

        # Внутри create_materials_screen
        add_btn = QPushButton("Добавить материал")
        add_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #67BA80; /* Заменили синий на зеленый по ТЗ */
                        color: #FFFFFF;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-height: 40px;
                    }
                    QPushButton:hover {
                        background-color: #559d6a; /* Темно-зеленый при наведении */
                    }
                """)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(lambda: QMessageBox.information(self, "Добавление", "Функция добавления материала"))
        control_panel.addWidget(add_btn)

        materials_layout.addLayout(control_panel)
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(8)
        self.materials_table.setHorizontalHeaderLabels([
            "ID", "Наименование", "Тип", "Поставщик", "Количество", "Мин. запас", "Стоимость", "Статус"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.load_materials_data()
        materials_layout.addWidget(self.materials_table)
        tabs.addTab(materials_tab, "Материалы на складе")

        low_stock_tab = QWidget()
        low_stock_layout = QVBoxLayout(low_stock_tab)
        low_stock_label = QLabel("Материалы с низким запасом")
        low_stock_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        low_stock_layout.addWidget(low_stock_label)
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(6)
        self.low_stock_table.setHorizontalHeaderLabels([
            "Наименование", "Тип", "Текущий запас", "Мин. запас", "Разница", "Статус"
        ])
        self.load_low_stock_data()
        low_stock_layout.addWidget(self.low_stock_table)
        tabs.addTab(low_stock_tab, "Низкие запасы")

        layout.addWidget(tabs)
        self.stacked_widget.addWidget(widget)

    def load_materials_data(self):
        materials = self.db.execute_query("""
            SELECT m.*, p.CompanyName as SupplierName 
            FROM materials m LEFT JOIN partners p ON m.SupplierID = p.PartnerID
            ORDER BY m.StockQuantity ASC
        """)
        self.materials_table.setRowCount(len(materials))
        for i, m in enumerate(materials):
            self.materials_table.setItem(i, 0, QTableWidgetItem(str(m['MaterialID'])))
            self.materials_table.setItem(i, 1, QTableWidgetItem(m['Name']))
            self.materials_table.setItem(i, 2, QTableWidgetItem(m['Type']))
            self.materials_table.setItem(i, 3, QTableWidgetItem(m['SupplierName'] or "Не указан"))
            self.materials_table.setItem(i, 4, QTableWidgetItem(f"{m['StockQuantity']} {m['Unit']}"))
            self.materials_table.setItem(i, 5, QTableWidgetItem(f"{m['MinStock']} {m['Unit']}"))
            self.materials_table.setItem(i, 6, QTableWidgetItem(f"{m['Cost']:,.2f} ₽"))
            status = "В норме" if m['StockQuantity'] >= m['MinStock'] else "Мало"
            status_item = QTableWidgetItem(status)
            if status == "В норме":
                status_item.setForeground(QColor("#67BA80"))
            else:
                status_item.setForeground(QColor("#E6A23C"))
            self.materials_table.setItem(i, 7, status_item)

    def load_low_stock_data(self):
        low_stock = self.db.execute_query("""
            SELECT m.*, p.CompanyName as SupplierName 
            FROM materials m LEFT JOIN partners p ON m.SupplierID = p.PartnerID
            WHERE m.StockQuantity < m.MinStock
            ORDER BY (m.StockQuantity - m.MinStock) ASC
        """)
        self.low_stock_table.setRowCount(len(low_stock))
        for i, m in enumerate(low_stock):
            self.low_stock_table.setItem(i, 0, QTableWidgetItem(m['Name']))
            self.low_stock_table.setItem(i, 1, QTableWidgetItem(m['Type']))
            self.low_stock_table.setItem(i, 2, QTableWidgetItem(f"{m['StockQuantity']} {m['Unit']}"))
            self.low_stock_table.setItem(i, 3, QTableWidgetItem(f"{m['MinStock']} {m['Unit']}"))
            diff = m['StockQuantity'] - m['MinStock']
            diff_item = QTableWidgetItem(f"{diff} {m['Unit']}")
            diff_item.setForeground(QColor("#E6A23C"))
            self.low_stock_table.setItem(i, 4, diff_item)
            status_item = QTableWidgetItem("Требует заказа")
            status_item.setForeground(QColor("#F56C6C"))
            self.low_stock_table.setItem(i, 5, status_item)

    def create_suppliers_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        control_panel = QHBoxLayout()
        self.supplier_search = QLineEdit()  # Проверьте наличие этой строки
        self.supplier_search.setPlaceholderText("🔍 Поиск поставщиков...")
        self.supplier_search.textChanged.connect(lambda text: self.universal_search(text, self.suppliers_table))
        self.supplier_search.setMinimumWidth(300)
        control_panel.addWidget(self.supplier_search)
        control_panel.addStretch()

        # Внутри create_materials_screen
        add_btn = QPushButton("Добавить поставщика")
        add_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #67BA80; /* Заменили синий на зеленый по ТЗ */
                        color: #FFFFFF;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-height: 40px;
                    }
                    QPushButton:hover {
                        background-color:  #67BA80; /* Темно-зеленый при наведении */
                    }
                """)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_supplier)
        control_panel.addWidget(add_btn)
        layout.addLayout(control_panel)

        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(8)
        self.suppliers_table.setHorizontalHeaderLabels([
            "ID", "Название компании", "Директор", "ИНН", "Телефон", "Email", "Рейтинг", "Поставляемые материалы"
        ])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_suppliers_data()
        layout.addWidget(self.suppliers_table)
        self.stacked_widget.addWidget(widget)

    def load_suppliers_data(self):
        suppliers = self.db.execute_query("""
            SELECT 
                p.PartnerID,
                p.CompanyName,
                p.DirectorName,
                p.INN,
                p.Phone,
                p.Email,
                p.Rating,
                GROUP_CONCAT(DISTINCT m.Name SEPARATOR ', ') AS SuppliedMaterials,
                COUNT(m.MaterialID) AS MaterialsCount
            FROM partners p
            LEFT JOIN materials m ON p.PartnerID = m.SupplierID
            WHERE TRIM(LOWER(p.Type)) = 'поставщик'
            GROUP BY 
                p.PartnerID,
                p.CompanyName,
                p.DirectorName,
                p.INN,
                p.Phone,
                p.Email,
                p.Rating
            ORDER BY p.Rating DESC, p.CompanyName
        """)
        self.suppliers_table.setRowCount(len(suppliers))
        for i, s in enumerate(suppliers):
            self.suppliers_table.setItem(i, 0, QTableWidgetItem(str(s['PartnerID'])))
            self.suppliers_table.setItem(i, 1, QTableWidgetItem(s['CompanyName'] or "—"))
            self.suppliers_table.setItem(i, 2, QTableWidgetItem(s['DirectorName'] or "—"))
            self.suppliers_table.setItem(i, 3, QTableWidgetItem(s['INN'] or "—"))
            self.suppliers_table.setItem(i, 4, QTableWidgetItem(s['Phone'] or "—"))
            self.suppliers_table.setItem(i, 5, QTableWidgetItem(s['Email'] or "—"))
            rating_item = QTableWidgetItem("★" * (s['Rating'] or 0))
            rating_item.setForeground(QColor("#E6A23C"))
            self.suppliers_table.setItem(i, 6, rating_item)
            materials = s['SuppliedMaterials'] or "Не указаны"
            materials_count = f"{materials} ({s['MaterialsCount']} видов)"
            self.suppliers_table.setItem(i, 7, QTableWidgetItem(materials_count))

    def add_supplier(self):
        d = PartnerDialog(self.db)
        d.type.setCurrentText("Поставщик")
        if d.exec_():
            self.load_suppliers_data()

    def create_analytics_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        kpi = QHBoxLayout()
        total_sales = self.db.execute_query("SELECT SUM(TotalAmount) s FROM orders")[0]["s"] or 0
        orders_cnt = self.db.execute_query("SELECT COUNT(*) c FROM orders")[0]["c"]
        partners_cnt = self.db.execute_query("SELECT COUNT(*) c FROM partners")[0]["c"]

        for title, value in [
            ("Общий доход", f"{total_sales:,.0f} ₽"),
            ("Заявок всего", str(orders_cnt)),
            ("Партнёров", str(partners_cnt))
        ]:
            box = QGroupBox(title)
            lbl = QLabel(value)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size:24px;font-weight:bold;")
            v = QVBoxLayout(box)
            v.addWidget(lbl)
            kpi.addWidget(box)
        layout.addLayout(kpi)

        top = QTableWidget(0, 2)
        top.setHorizontalHeaderLabels(["Партнёр", "Продажи"])
        style_table(top)
        data = self.db.execute_query("""
            SELECT p.CompanyName, SUM(o.TotalAmount) total
            FROM orders o
            JOIN partners p ON p.PartnerID = o.PartnerID
            GROUP BY p.PartnerID
            ORDER BY total DESC
            LIMIT 5
        """)
        top.setRowCount(len(data))
        for r, d in enumerate(data):
            top.setItem(r, 0, QTableWidgetItem(d["CompanyName"]))
            top.setItem(r, 1, QTableWidgetItem(f'{d["total"]:,.0f} ₽'))
        layout.addWidget(QLabel("ТОП партнёров по продажам"))
        layout.addWidget(top)

        low = QTableWidget(0, 3)
        low.setHorizontalHeaderLabels(["Материал", "Текущий", "Минимум"])
        style_table(low)
        data = self.db.execute_query("""
            SELECT Name, StockQuantity, MinStock
            FROM materials
            WHERE StockQuantity < MinStock
        """)
        low.setRowCount(len(data))
        for r, m in enumerate(data):
            low.setItem(r, 0, QTableWidgetItem(m["Name"]))
            low.setItem(r, 1, QTableWidgetItem(str(m["StockQuantity"])))
            low.setItem(r, 2, QTableWidgetItem(str(m["MinStock"])))
        layout.addWidget(QLabel("Материалы с низким запасом"))
        layout.addWidget(low)

        self.stacked_widget.addWidget(widget)

    def show_main(self):
        self.stacked_widget.setCurrentIndex(0)
        self.title_label.setText("Главная панель")
        self.update_nav_buttons(0)

    def show_partners(self):
        self.stacked_widget.setCurrentIndex(1)
        self.title_label.setText("Управление партнерами")
        self.update_nav_buttons(1)
        self.load_partners_data()

    def show_products(self):
        self.stacked_widget.setCurrentIndex(2)
        self.title_label.setText("Каталог продукции")
        self.update_nav_buttons(2)
        self.load_products_data()

    def show_orders(self):
        self.stacked_widget.setCurrentIndex(3)
        self.title_label.setText("Управление заявками")
        self.update_nav_buttons(4)
        self.load_orders_data()

    def show_employees(self):
        self.stacked_widget.setCurrentIndex(4)
        self.title_label.setText("Сотрудники")
        self.update_nav_buttons(5)

    def show_materials(self):
        self.stacked_widget.setCurrentIndex(5)
        self.title_label.setText("Управление материалами")
        self.update_nav_buttons(6)
        self.load_materials_data()
        self.load_low_stock_data()

    def show_suppliers(self):
        self.stacked_widget.setCurrentIndex(6)
        self.title_label.setText("Поставщики")
        self.update_nav_buttons(8)
        self.load_suppliers_data()

    def show_analytics(self):
        self.stacked_widget.setCurrentIndex(7)
        self.title_label.setText("Аналитика")
        self.update_nav_buttons(9)

    def show_production(self):
        self.show_main()

    def show_warehouse(self):
        self.show_main()

    def update_nav_buttons(self, active_index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("class", "sidebar-button" + (" active" if i == active_index else ""))


def main():
    app = QApplication(sys.argv)
    app_icon = QIcon("./res/Мастер пол.ico")
    app.setWindowIcon(app_icon)
    QFontDatabase = QFont("Segoe UI")
    app.setFont(QFontDatabase)
    db = DatabaseManager()
    auth = AuthDialog(db)
    if auth.exec_() == QDialog.Accepted:
        window = MainWindow(auth.logged_in_user)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
