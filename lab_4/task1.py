from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time
import uuid
 
 
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
    """Фільм із закріпленим залом."""
    title: str
    genre: MovieGenre
    duration_min: int
    hall: Hall
 
    def __post_init__(self):
        if self.duration_min <= 0:
            raise ValueError("Тривалість фільму повинна бути більшою за 0 хвилин!")
 
 
# Автоматичний розподіл залів за жанрами
GENRE_HALLS_MAP = {
    MovieGenre.ACTION: Hall("Hall 1", "Action Arena: Abandon All Hope, Ye Who Enter", 120),
    MovieGenre.COMEDY: Hall("Hall 2", "Laughter Hub: Ho-Ho-Ho, But Not Santa", 100),
    MovieGenre.SCI_FI: Hall("Hall 3", "Sci-Fi Dimension: Become Part of a New World", 150),
    MovieGenre.DRAMA: Hall("Hall 4", "Tears Theater: Free Tissues, No Registration Required", 80),
}
 
BOOKING_TIMEOUT_SEC = 60
 
 
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
        return (f"Квиток [{self.ticket_id}] '{self.movie.title}', місце {self.seat} — "
                f"{self.calculate_final_price():.2f} UAH [{self.status.value}]")
 
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
        print(f" Hall         : {self.movie.hall.name}")
        print(f" Hall Vibe    : {self.movie.hall.vibe_description}")
        print(f" Seat         : {self.seat}")
        print(f" Ticket Type  : {self.get_type_label()}")
        print(f" Status       : {self.status.value}")
        print(f" Final Price  : {self.calculate_final_price():.2f} UAH")
        print("=" * 55)
 
 
# 4. Класи-нащадки
class VIPTicket(Ticket):
    """VIP-квиток: націнка 50% та доступ до лаунж-зони."""
    RECEIPT_TITLE = "👑 VIP CINEMA TICKET RECEIPT 👑"
 
    def __init__(self, movie: Movie, base_price: float, seat: str, lounge_access: bool = True):
        super().__init__(movie, base_price, seat)
        self.lounge_access = lounge_access
 
    def calculate_final_price(self) -> float:
        return self.base_price * 1.5
 
    def get_type_label(self) -> str:
        return f"VIP Ticket (+ Lounge Access: {'Yes' if self.lounge_access else 'No'})"
 
 
class StudentTicket(Ticket):
    """Студентський квиток: знижка 30%."""
    RECEIPT_TITLE = "🎓 STUDENT CINEMA TICKET RECEIPT 🎓"
 
    def __init__(self, movie: Movie, base_price: float, seat: str, student_card_id: str):
        super().__init__(movie, base_price, seat)
        self.student_card_id = student_card_id
 
    def calculate_final_price(self) -> float:
        return self.base_price * 0.7
 
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
        self.start_time = time.time()
        print(f"\n[⏱️ SYSTEM] Сесію бронювання розпочато. Ліміт часу: {self.timeout_seconds} сек.")
        return self
 
    def __exit__(self, exc_type, exc_val, traceback) -> bool:
        if self.ticket is None:
            return False
        elapsed_time = time.time() - self.start_time
        print(f"[⏱️ SYSTEM] Витрачено часу: {elapsed_time:.2f} сек.")
        if elapsed_time > self.timeout_seconds:
            self.ticket.status = TicketStatus.EXPIRED
            print("[❌] Час бронювання вичерпано! Статус квитка: Expired.")
        return False
 
 
# 6. Клас-менеджер (Композиція)
class CinemaManager:
    """Містить колекцію оплачених квитків."""
    def __init__(self):
        self.__tickets: list[Ticket] = []
 
    def add_ticket(self, ticket: Ticket) -> None:
        self.__tickets.append(ticket)
 
    def __len__(self) -> int:
        return len(self.__tickets)
 
    def __iter__(self):
        """Ітерація від найдорожчих квитків до найдешевших."""
        return iter(sorted(self.__tickets, key=lambda t: t.calculate_final_price(), reverse=True))
 
    def show_sorted_archive(self) -> None:
        print("\n" + "#" * 55)
        print("ARCHIVE: TICKETS (SORTED BY PRICE: HIGH -> LOW)".center(55))
        print("#" * 55)
        if not self:
            print("Архів порожній. Ще не було оформлено жодного квитка.")
            return
        print(f"Всього квитків: {len(self)}")
        for ticket in self:
            ticket.print_ticket_stub()
 
 
def print_batch_receipt(movie: Movie, tickets: list[Ticket]) -> None:
    print("\n" + "=" * 55)
    print("🎬 ФІНАЛЬНИЙ ЗВЕДЕНИЙ ЧЕК ЗАМОВЛЕННЯ 🎬".center(55))
    print("=" * 55)
    print(f" Фільм : {movie.title} ({movie.genre.value})")
    print(f" Зал   : {movie.hall.name}")
    for ticket in tickets:
        print(f" {ticket}")
    print("-" * 55)
    print(f" ЗАГАЛЬНА СУМА ДО СПЛАТИ: {sum(tickets):.2f} UAH")
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
 
 
def create_movie() -> Movie:
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
    return Movie(title, genre, duration, hall)
 
 
def create_ticket(choice: str, movie: Movie) -> Ticket:
    seat = input("Введіть номер місця (наприклад, A-12): ")
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
    print(f"Поточний сеанс: {movie.title} ({movie.hall.name})")
    print("1. Звичайний квиток (Standard)")
    print("2. ВІП-квиток (VIP)")
    print("3. Студентський квиток (Student)")
    print("4. Завершити замовлення та отримати чек")
 
    while True:
        choice = input("Оберіть опцію (1-4): ").strip()
        if choice in ("1", "2", "3", "4"):
            return choice
        print("[ПОМИЛКА] Невірний вибір. Введіть число від 1 до 4.")
 
 
def book_ticket(movie: Movie) -> Optional[Ticket]:
    """Одна сесія бронювання під таймером. Повертає None, якщо клієнт завершує замовлення."""
    with TicketBookingContext(BOOKING_TIMEOUT_SEC) as booking:
        choice = read_ticket_choice(movie)
        if choice == "4":
            return None
 
        booking.ticket = create_ticket(choice, movie)
        paid = ask_yes("Підтвердити оплату? (так/ні): ")
        booking.ticket.status = TicketStatus.PAID if paid else TicketStatus.CANCELLED
    return booking.ticket
 
 
def ticket_menu(movie: Movie, manager: CinemaManager) -> None:
    session_tickets = []
 
    while True:
        try:
            ticket = book_ticket(movie)
            if ticket is None:
                break
            if ticket.status == TicketStatus.PAID:
                session_tickets.append(ticket)
                manager.add_ticket(ticket)
                print(f"[OK] Додано до замовлення: {ticket}")
            else:
                print(f"[!] Квиток не додано до замовлення. Статус: {ticket.status.value}")
        except ValueError as e:
            print(f"\n[ПОМИЛКА ВАЛІДАЦІЇ] {e}")
 
        if not ask_yes("\nБажаєте оформити ще квиток? (так/ні): "):
            break
 
    if session_tickets:
        print_batch_receipt(movie, session_tickets)
        print("\nДякуємо за покупку! Приємного перегляду 🍿🎬")
    else:
        print("\nЗамовлення завершено без квитків.")
 
 
# --- Блок демонстрації (Main CLI) ---
if __name__ == "__main__":
    print("--- Cinema System CLI: Система управління кінотеатром ---")
    manager = CinemaManager()
    current_movie = None
 
    while True:
        print("\n" + "=" * 40)
        print("ГОЛОВНЕ МЕНЮ".center(40))
        print("=" * 40)
        print("1. Замовити квитки (Кошик клієнта)")
        print("2. Переглянути архів (Тільки для менеджера)")
        print("3. Вихід з програми")
 
        main_choice = input("Оберіть дію (1-3): ").strip()
 
        try:
            if main_choice == "1":
                if current_movie is None:
                    current_movie = create_movie()
                ticket_menu(current_movie, manager)
            elif main_choice == "2":
                manager.show_sorted_archive()
            elif main_choice == "3":
                print("\nРоботу системи завершено. До зустрічі! 👋")
                break
            else:
                print("[ПОМИЛКА] Невірний вибір. Будь ласка, введіть число від 1 до 3.")
        except ValueError as e:
            print(f"\n[ПОМИЛКА ВАЛІДАЦІЇ] {e}")
        except Exception as e:
            print(f"\n[ПОМИЛКА] Виникла непередбачувана ситуація: {e}")
 