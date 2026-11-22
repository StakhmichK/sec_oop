from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from itertools import groupby
from typing import Optional
import csv
import json
import os
import pickle
import string
import time as time_module
import uuid


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.dirname(BASE_DIR)
CONFIG_FILE = os.path.join(BASE_DIR, "lab_config.json")

DEFAULT_CONFIG = {
    "cinema_name": "Cinema System CLI",
    "booking_timeout_sec": 60,
    "seats_per_row": 10,
    "pricing": {
        "service_fee_rate": 0.05,
        "vip_multiplier": 1.5,
        "student_discount": 0.7,
    },
    "paths": {
        "lab_data": "lab_data.pkl",
        "lab_reports": "lab_reports.csv",
    },
}

def _resolve_shared_path(path_value: str) -> str:
    """Абсолютний шлях лишає як є, а відносний бере від спільної папки sec_oop."""
    if os.path.isabs(path_value):
        return path_value
    return os.path.normpath(os.path.join(SHARED_DIR, path_value))


def _deep_merge(base: dict, override: dict) -> dict:
    """Рекурсивно об'єднує дефолтний конфіг із даними з JSON (підтримує вкладені словники)."""
    result = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_lab_config(filepath: str = CONFIG_FILE) -> dict:
    """Читає зовнішні налаштування з JSON при старті (або створює дефолтний файл)."""
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
        print(f"[⚙️ JSON] Створено стандартний конфіг: {filepath}")
        return _deep_merge(DEFAULT_CONFIG, {})

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError("Кореневий елемент JSON повинен бути об'єктом")
        merged = _deep_merge(DEFAULT_CONFIG, loaded)
        print(f"[⚙️ JSON] Завантажено конфіг '{filepath}' ({merged['cinema_name']}).")
        return merged
    except Exception as e:
        print(f"[⚠️ JSON] Помилка читання {filepath} ({e}). Використано значення за замовчуванням.")
        return _deep_merge(DEFAULT_CONFIG, {})


LAB_CONFIG = load_lab_config()
LAB_DATA_FILE = _resolve_shared_path(str(LAB_CONFIG["paths"]["lab_data"]))
LAB_REPORT_FILE = _resolve_shared_path(str(LAB_CONFIG["paths"]["lab_reports"]))
BOOKING_TIMEOUT_SEC = int(LAB_CONFIG["booking_timeout_sec"])
SERVICE_FEE_RATE = float(LAB_CONFIG["pricing"]["service_fee_rate"])
VIP_MULTIPLIER = float(LAB_CONFIG["pricing"]["vip_multiplier"])
STUDENT_DISCOUNT = float(LAB_CONFIG["pricing"]["student_discount"])
SEATS_PER_ROW = int(LAB_CONFIG["seats_per_row"])


# 1. Перелічувані типи (Enum)
class MovieGenre(Enum):
    ACTION = "Бойовик"
    COMEDY = "Комедія"
    SCI_FI = "Фантастика"
    DRAMA = "Драма"


class TicketStatus(Enum):
    BOOKED = "Заброньовано"
    PAID = "Оплачено"
    CANCELLED = "Скасовано"
    EXPIRED = "Expired"


# 2. Структури даних (dataclass)
@dataclass
class Hall:
    """Зал кінотеатру."""
    name: str
    vibe_description: str
    capacity: int


@dataclass
class Movie:
    """Фільм із закріпленим залом та часом сеансу."""
    title: str
    genre: MovieGenre
    duration_min: int
    hall: Hall
    start_time: datetime

    def __post_init__(self):
        if self.duration_min <= 0:
            raise ValueError("Тривалість фільму повинна бути більшою за 0 хвилин!")


# Автоматичний розподіл залів за жанрами
GENRE_HALLS_MAP = {
    MovieGenre.ACTION: Hall("Hall 1", "Action Arena: Abandon All Hope, Ye Who Enter", 50),
    MovieGenre.COMEDY: Hall("Hall 2", "Laughter Hub: Ho-Ho-Ho, But Not Santa", 70),
    MovieGenre.SCI_FI: Hall("Hall 3", "Sci-Fi Dimension: Become Part of a New World", 100),
    MovieGenre.DRAMA: Hall("Hall 4", "Tears Theater: Free Tissues, No Registration Required", 80),
}

# Сітка базових сеансів на кожен день
TIME_SLOTS = [time(10, 0), time(11, 30), time(13, 0), time(14, 30), time(16, 0),
              time(17, 30), time(19, 0), time(20, 30), time(22, 0), time(23, 30)]


# 3. Базовий клас
class Ticket:
    """Звичайний квиток у кіно."""
    RECEIPT_TITLE = "🎬 CINEMA TICKET RECEIPT 🎬"

    def __init__(self, movie: Movie, base_price: float, seat: str,
                 status: TicketStatus = TicketStatus.BOOKED):
        self.__id = str(uuid.uuid4())[:8]
        self.movie = movie
        self.status = status
        self.seat = seat
        self.base_price = base_price

    @property
    def ticket_id(self) -> str:
        return self.__id

    @property
    def base_price(self) -> float:
        return self.__base_price

    @base_price.setter
    def base_price(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Базова ціна квитка повинна бути числом!")
        if value <= 0:
            raise ValueError("Базова ціна квитка повинна бути більшою за 0 грн!")
        self.__base_price = float(value)

    @property
    def seat(self) -> str:
        return self.__seat

    @seat.setter
    def seat(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Номер місця повинен бути рядком!")
        cleaned_value = value.strip().upper()
        # Місце має містити і літеру, і цифру
        if not (any(c.isalpha() for c in cleaned_value) and any(c.isdigit() for c in cleaned_value)):
            raise ValueError("Невірний формат місця! Приклад правильного місця: 'A-12' або 'Б-5'.")
        self.__seat = cleaned_value

    # Поліморфні методи (перевизначаються в нащадках)
    def calculate_final_price(self) -> float:
        return self.base_price

    def get_type_label(self) -> str:
        return "Standard Ticket"

    # Магічні методи
    def __str__(self) -> str:
        return (f"Квиток [{self.ticket_id}] '{self.movie.title}' "
                f"({self.movie.start_time:%d.%m.%Y %H:%M}), місце {self.seat} — "
                f"{self.calculate_final_price():.2f} UAH [{self.status.value}]")

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(id='{self.ticket_id}', seat='{self.seat}', "
                f"price={self.calculate_final_price():.2f})")

    def __add__(self, other):
        if isinstance(other, Ticket):
            return self.calculate_final_price() + other.calculate_final_price()
        if isinstance(other, (int, float)):
            return self.calculate_final_price() + other
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def print_ticket_stub(self) -> None:
        print("\n" + "=" * 55)
        print(self.RECEIPT_TITLE.center(55))
        print("=" * 55)
        print(f" Ticket ID    : {self.ticket_id}")
        print(f" Movie        : {self.movie.title} ({self.movie.genre.value})")
        print(f" Date & Time  : {self.movie.start_time:%d.%m.%Y %H:%M}")
        print(f" Hall         : {self.movie.hall.name}")
        print(f" Hall Vibe    : {self.movie.hall.vibe_description}")
        print(f" Seat         : {self.seat}")
        print(f" Ticket Type  : {self.get_type_label()}")
        print(f" Status       : {self.status.value}")
        print(f" Final Price  : {self.calculate_final_price():.2f} UAH")
        print("=" * 55)


# 4. Класи-нащадки
class VIPTicket(Ticket):
    """VIP-квиток: націнка з конфігу та доступ до лаунж-зони."""
    RECEIPT_TITLE = "👑 VIP CINEMA TICKET RECEIPT 👑"

    def __init__(self, movie: Movie, base_price: float, seat: str, lounge_access: bool = True):
        super().__init__(movie, base_price, seat)
        self.lounge_access = lounge_access

    def calculate_final_price(self) -> float:
        return self.base_price * VIP_MULTIPLIER

    def get_type_label(self) -> str:
        return f"VIP Ticket (+ Lounge Access: {'Yes' if self.lounge_access else 'No'})"


class StudentTicket(Ticket):
    """Студентський квиток: знижка з конфігу."""
    RECEIPT_TITLE = "🎓 STUDENT CINEMA TICKET RECEIPT 🎓"

    def __init__(self, movie: Movie, base_price: float, seat: str, student_card_id: str):
        super().__init__(movie, base_price, seat)
        self.student_card_id = student_card_id

    def calculate_final_price(self) -> float:
        return self.base_price * STUDENT_DISCOUNT

    def get_type_label(self) -> str:
        return f"Student Ticket (ID: {self.student_card_id})"


# 5. Контекстний менеджер бронювання (Time-Out)
class TicketBookingContext:
    """Якщо оформлення квитка тривало довше за timeout_seconds, він отримує статус Expired."""
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.start_time = 0.0
        self.ticket = None

    def __enter__(self):
        self.start_time = time_module.time()
        print(f"\n[⏱️ SYSTEM] Сесію бронювання розпочато. Ліміт часу: {self.timeout_seconds} сек.")
        return self

    def __exit__(self, exc_type, exc_val, traceback) -> bool:
        if self.ticket is None:
            return False
        elapsed_time = time_module.time() - self.start_time
        print(f"[⏱️ SYSTEM] Витрачено часу: {elapsed_time:.2f} сек.")
        if elapsed_time > self.timeout_seconds:
            self.ticket.status = TicketStatus.EXPIRED
            print("[❌] Час бронювання вичерпано! Статус квитка: Expired.")
        return False


# 6. Функтор (бізнес-логіка зі станом)
class TicketPricingFunctor:
    """Нараховує сервісний збір до квитка та запам'ятовує, скільки зборів уже стягнуто."""
    def __init__(self, fee_rate: float):
        self.fee_rate = fee_rate
        self.calls_count = 0
        self.total_fees = 0.0

    def __call__(self, ticket: Ticket) -> float:
        fee = ticket.calculate_final_price() * self.fee_rate
        self.calls_count += 1
        self.total_fees += fee
        return ticket + fee


# 7. Кастомний ітератор (актуальні сеанси)
class AvailableSlotIterator:
    """Пропускає часові слоти, які на обрану дату вже минули за часом пристрою."""
    def __init__(self, slots: list[time], chosen_date: date):
        self._slots = slots
        self._chosen_date = chosen_date
        self._now = datetime.now()
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self) -> time:
        while self._index < len(self._slots):
            slot = self._slots[self._index]
            self._index += 1
            if datetime.combine(self._chosen_date, slot) > self._now:
                return slot
        raise StopIteration


# 8. Клас-менеджер (Композиція + збереження/експорт)
class CinemaManager:
    """Журнал бронювань і сітка сеансів. Містить функтор, віддає слоти ітератором, а місця генератором."""
    def __init__(self):
        self.__tickets: list[Ticket] = []
        self.__time_slots = list(TIME_SLOTS)
        self.pricing_functor = TicketPricingFunctor(SERVICE_FEE_RATE)

    def add_ticket(self, ticket: Ticket) -> None:
        self.__tickets.append(ticket)

    def __len__(self) -> int:
        return len(self.__tickets)

    def __iter__(self):
        """Усі записи від найдорожчих до найдешевших."""
        return iter(sorted(self.__tickets, key=lambda t: t.calculate_final_price(), reverse=True))

    def get_available_slots(self, chosen_date: date) -> AvailableSlotIterator:
        return AvailableSlotIterator(self.__time_slots, chosen_date)

    def generate_free_seats(self, movie: Movie):
        """Генератор: по одному видає місця залу, які ще не куплені на цей сеанс."""
        occupied_seats = {
            ticket.seat for ticket in self.__tickets
            if ticket.movie == movie and ticket.status == TicketStatus.PAID
        }
        rows_count = movie.hall.capacity // SEATS_PER_ROW
        for row_letter in string.ascii_uppercase[:rows_count]:
            for number in range(1, SEATS_PER_ROW + 1):
                seat = f"{row_letter}-{number}"
                if seat not in occupied_seats:
                    yield seat

    def save_lab_data(self, filepath: str = LAB_DATA_FILE) -> None:
        """Зберігає повний стан менеджера у бінарний файл через pickle."""
        data_dir = os.path.dirname(filepath)
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
        with open(filepath, "wb") as file:
            pickle.dump(self, file)
        print(f"[💾 lab_data] Стан системи збережено у '{filepath}'.")

    @classmethod
    def load_lab_data(cls, filepath: str = LAB_DATA_FILE) -> "CinemaManager":
        """Відновлює стан менеджера з бінарного файлу pickle або створює новий."""
        if not os.path.exists(filepath):
            print(f"[💾 lab_data] Файл '{filepath}' ще не створено. Стартуємо з чистою базою.")
            return cls()
        try:
            with open(filepath, "rb") as file:
                restored = pickle.load(file)
            restored.pricing_functor.fee_rate = SERVICE_FEE_RATE
            print(f"[💾 lab_data] Відновлено стан із '{filepath}' (записів: {len(restored)}).")
            return restored
        except Exception as e:
            print(f"[⚠️ lab_data] Не вдалося прочитати '{filepath}' ({e}). Створено новий менеджер.")
            return cls()

    def export_lab_reports(self, filepath: str = LAB_REPORT_FILE) -> None:
        """Експортує оплачені квитки у CSV (табуляція + UTF-16 для коректного відкриття в Excel)."""
        paid_tickets = [t for t in self if t.status == TicketStatus.PAID]
        if not paid_tickets:
            print("[⚠️ lab_reports] Немає оплачених квитків для експорту в CSV.")
            return

        report_dir = os.path.dirname(filepath)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)

        try:
            with open(filepath, "w", newline="", encoding="utf-16") as file:
                writer = csv.writer(file, delimiter="\t")
                writer.writerow([
                    "ID квитка",
                    "Фільм",
                    "Жанр",
                    "Дата й час сеансу",
                    "Зал",
                    "Місце",
                    "Тип квитка",
                    "Базова ціна (UAH)",
                    "Ціна квитка (UAH)",
                    "З урахуванням збору (UAH)",
                ])
                for t in paid_tickets:
                    with_fee = t.calculate_final_price() * (1 + self.pricing_functor.fee_rate)
                    writer.writerow([
                        t.ticket_id,
                        t.movie.title,
                        t.movie.genre.value,
                        f"{t.movie.start_time:%d.%m.%Y %H:%M}",
                        t.movie.hall.name,
                        t.seat,
                        t.get_type_label(),
                        f"{t.base_price:.2f}",
                        f"{t.calculate_final_price():.2f}",
                        f"{with_fee:.2f}",
                    ])
        except PermissionError:
            print(f"\n[❌ ПОМИЛКА] Файл '{filepath}' зараз відкритий в Excel! Закрий його та спробуй ще раз.")
            return

        print(f"[📊 lab_reports] CSV-звіт сформовано у '{filepath}' (рядків: {len(paid_tickets)}).")

    def show_sorted_archive(self) -> None:
        print("\n" + "#" * 55)
        print("ARCHIVE: PAID TICKETS (HIGH -> LOW)".center(55))
        print("#" * 55)
        if not self:
            print("Журнал порожній. Ще не було жодної спроби бронювання.")
            return
        paid_tickets = [ticket for ticket in self if ticket.status == TicketStatus.PAID]
        for ticket in paid_tickets:
            ticket.print_ticket_stub()
        print(f"\n[ЖУРНАЛ] Записів: {len(self)}, з них оплачених: {len(paid_tickets)}")
        print(f"[ФУНКТОР] Зборів нараховано: {self.pricing_functor.calls_count} разів, "
              f"разом {self.pricing_functor.total_fees:.2f} UAH")


def print_free_seats(manager: CinemaManager, movie: Movie) -> None:
    print("\nВільні місця (куплені зникають зі списку):")
    for _, row_seats in groupby(manager.generate_free_seats(movie), key=lambda seat: seat.split("-")[0]):
        print(" ".join(f"{seat:<4}" for seat in row_seats))


def print_batch_receipt(movie: Movie, tickets: list[Ticket], total_due: float) -> None:
    subtotal = sum(tickets)
    print("\n" + "=" * 55)
    print("🎬 ФІНАЛЬНИЙ ЗВЕДЕНИЙ ЧЕК ЗАМОВЛЕННЯ 🎬".center(55))
    print("=" * 55)
    print(f" Фільм : {movie.title} ({movie.genre.value})")
    print(f" Сеанс : {movie.start_time:%d.%m.%Y %H:%M}")
    print(f" Зал   : {movie.hall.name}")
    for ticket in tickets:
        print(f" {ticket}")
    print("-" * 55)
    print(f" Сума квитків    : {subtotal:.2f} UAH")
    print(f" Сервісний збір  : {total_due - subtotal:.2f} UAH")
    print(f" ЗАГАЛЬНА СУМА ДО СПЛАТИ: {total_due:.2f} UAH")
    print("=" * 55)


# --- Допоміжні функції CLI ---
YES_ANSWERS = ("так", "yes", "y", "+")

GENRE_CHOICES = {
    "1": MovieGenre.ACTION,
    "2": MovieGenre.COMEDY,
    "3": MovieGenre.SCI_FI,
    "4": MovieGenre.DRAMA,
}


def ask_yes(prompt: str) -> bool:
    return input(prompt).strip().lower() in YES_ANSWERS


def choose_start_time(manager: CinemaManager) -> datetime:
    print("\n=== Вибір дати та часу сеансу ===")
    date_str = input("Введіть дату сеансу (ДД.ММ.РРРР, напр. 20.11.2026): ").strip()
    try:
        chosen_date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise ValueError("Некоректна дата! Введіть дату у форматі ДД.ММ.РРРР (наприклад, 20.11.2026).")

    slots = list(manager.get_available_slots(chosen_date))
    if not slots:
        raise ValueError("На цю дату вже немає доступних сеансів!")

    print("Доступні сеанси:")
    for number, slot in enumerate(slots, 1):
        print(f"[{number}] {slot:%H:%M}")
    choice = input(f"Оберіть час сеансу (1-{len(slots)}): ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(slots):
        raise ValueError("Невірний вибір часу сеансу!")
    return datetime.combine(chosen_date, slots[int(choice) - 1])


def create_movie(manager: CinemaManager) -> Movie:
    print("\n=== Налаштування кіносеансу ===")
    title = input("Введіть назву фільму: ").strip()

    print("Виберіть жанр:")
    print("1 - Бойовик\n2 - Комедія\n3 - Фантастика\n4 - Драма")
    genre = GENRE_CHOICES.get(input("Введіть номер жанру (1-4): ").strip())
    if genre is None:
        raise ValueError("Невірний вибір жанру!")

    hall = GENRE_HALLS_MAP[genre]
    print(f"\n[АВТО-РОЗПОДІЛ] Фільм закріплено за залом: {hall.name}")
    print(f"Вайб залу: \"{hall.vibe_description}\"")

    duration = int(input("Введіть тривалість фільму (хв): "))
    return Movie(title, genre, duration, hall, choose_start_time(manager))


def choose_movie(current_movie: Optional[Movie], manager: CinemaManager) -> Movie:
    if current_movie is None:
        return create_movie(manager)

    print(f"\n1. Продовжити замовлення на «{current_movie.title}» ({current_movie.start_time:%d.%m.%Y %H:%M})")
    print("2. Замовити квиток на новий сеанс")
    while True:
        choice = input("Оберіть опцію (1-2): ").strip()
        if choice == "1":
            return current_movie
        if choice == "2":
            return create_movie(manager)
        print("[ПОМИЛКА] Невірний вибір. Введіть 1 або 2.")


def create_ticket(choice: str, movie: Movie, manager: CinemaManager) -> Ticket:
    if next(manager.generate_free_seats(movie), None) is None:
        raise ValueError("На цей сеанс більше немає вільних місць!")

    print_free_seats(manager, movie)
    seat = input("\nВведіть номер вільного місця (наприклад, A-5): ").strip().upper()
    if seat not in manager.generate_free_seats(movie):
        raise ValueError(f"Місце '{seat}' зайняте або не існує в цьому залі!")
    price = float(input("Введіть базову ціну квитка (грн): "))

    if choice == "1":
        return Ticket(movie, price, seat)
    if choice == "2":
        lounge = ask_yes("Бажаєте доступ до лаунж-зони? (так/ні): ")
        return VIPTicket(movie, price, seat, lounge)
    student_id = input("Введіть номер студентського квитка: ")
    return StudentTicket(movie, price, seat, student_id)


def read_ticket_choice(movie: Movie) -> str:
    print("\n=== Меню оформлення квитка ===")
    print(f"Поточний сеанс: {movie.title} | {movie.hall.name} | {movie.start_time:%d.%m.%Y %H:%M}")
    print("1. Звичайний квиток (Standard)")
    print("2. ВІП-квиток (VIP)")
    print("3. Студентський квиток (Student)")
    print("4. Завершити замовлення та отримати чек")

    while True:
        choice = input("Оберіть опцію (1-4): ").strip()
        if choice in ("1", "2", "3", "4"):
            return choice
        print("[ПОМИЛКА] Невірний вибір. Введіть число від 1 до 4.")


def book_ticket(movie: Movie, manager: CinemaManager) -> Optional[Ticket]:
    """Одна сесія бронювання під таймером. Повертає None, якщо клієнт завершує замовлення."""
    with TicketBookingContext(BOOKING_TIMEOUT_SEC) as booking:
        choice = read_ticket_choice(movie)
        if choice == "4":
            return None

        booking.ticket = create_ticket(choice, movie, manager)
        paid = ask_yes("Підтвердити оплату? (так/ні): ")
        booking.ticket.status = TicketStatus.PAID if paid else TicketStatus.CANCELLED
    return booking.ticket


def ticket_menu(movie: Movie, manager: CinemaManager) -> None:
    session_tickets = []
    session_total = 0.0

    while True:
        try:
            ticket = book_ticket(movie, manager)
            if ticket is None:
                break
            manager.add_ticket(ticket)
            if ticket.status == TicketStatus.PAID:
                amount_due = manager.pricing_functor(ticket)
                session_tickets.append(ticket)
                session_total += amount_due
                print(f"[OK] Додано до замовлення: {ticket} | З урахуванням збору: {amount_due:.2f} UAH")
            else:
                print(f"[!] Квиток не оплачено. Статус: {ticket.status.value}")
        except ValueError as e:
            print(f"\n[ПОМИЛКА ВАЛІДАЦІЇ] {e}")

        if not ask_yes("\nБажаєте оформити ще квиток? (так/ні): "):
            break

    if session_tickets:
        manager.save_lab_data()
        print_batch_receipt(movie, session_tickets, session_total)
        print("\nДякуємо за покупку! Приємного перегляду 🍿🎬")
    else:
        print("\nЗамовлення завершено без оплачених квитків.")


# --- Блок демонстрації (Main CLI) ---
if __name__ == "__main__":
    print(f"--- {LAB_CONFIG['cinema_name']}: Система управління кінотеатром ---")
    manager = CinemaManager.load_lab_data()
    current_movie = None

    while True:
        print("\n" + "=" * 40)
        print("ГОЛОВНЕ МЕНЮ".center(40))
        print("=" * 40)
        print("1. Замовити квитки (Кошик клієнта)")
        print("2. Переглянути архів оплачених квитків (Функтор)")
        print("3. Зберегти стан у бінарний файл (lab_data)")
        print("4. Експортувати звіт у CSV (lab_reports)")
        print("5. Вихід з програми")

        main_choice = input("Оберіть дію (1-5): ").strip()

        try:
            if main_choice == "1":
                current_movie = choose_movie(current_movie, manager)
                ticket_menu(current_movie, manager)
            elif main_choice == "2":
                manager.show_sorted_archive()
            elif main_choice == "3":
                manager.save_lab_data()
            elif main_choice == "4":
                manager.export_lab_reports()
            elif main_choice == "5":
                manager.save_lab_data()
                print("\nРоботу системи завершено. До зустрічі! 👋")
                break
            else:
                print("[ПОМИЛКА] Невірний вибір. Будь ласка, введіть число від 1 до 5.")
        except ValueError as e:
            print(f"\n[ПОМИЛКА ВАЛІДАЦІЇ] {e}")
        except Exception as e:
            print(f"\n[ПОМИЛКА] Виникла непередбачувана ситуація: {e}")