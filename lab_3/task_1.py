from dataclasses import dataclass
from enum import Enum
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

# 3. Базовий клас
class Ticket:
    """Звичайний квиток у кіно."""
    RECEIPT_TITLE = "🎬 CINEMA TICKET RECEIPT 🎬"

    def __init__(self, movie: Movie, base_price: float, seat: str,
                 status: TicketStatus = TicketStatus.PAID):
        self.__id = str(uuid.uuid4())[:8]
        self.movie = movie
        self.status = status
        self.seat = seat
        self.base_price = base_price  # Виклик сетера для валідації

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
        if not isinstance(value, str) or len(value.strip()) < 2:
            raise ValueError("Номер місця має містити щонайменше 2 символи (наприклад, 'A-12')!")
        self.__seat = value.strip().upper()

    # Поліморфні методи (перевизначаються в нащадках)
    def calculate_final_price(self) -> float:
        return self.base_price

    def get_type_label(self) -> str:
        return "Standard Ticket"

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

# 5. Клас-менеджер
class CinemaManager:
    """Містить колекцію квитків."""
    def __init__(self):
        self.__tickets: list[Ticket] = []

    def add_ticket(self, ticket: Ticket) -> None:
        self.__tickets.append(ticket)
        ticket.print_ticket_stub()

    def show_all_tickets(self) -> None:
        print("\n" + "#" * 55)
        print("ARCHIVE: ALL BOOKED TICKETS".center(55))
        print("#" * 55)
        if not self.__tickets:
            print("Архів порожній. Ще не було оформлено жодного квитка.")
        for ticket in self.__tickets:
            ticket.print_ticket_stub()

# --- Допоміжні функції ---
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

def ticket_menu(movie: Movie, manager: CinemaManager) -> None:
    while True:
        print("\n=== Меню оформлення квитка ===")
        print(f"Поточний сеанс: {movie.title} ({movie.hall.name})")
        print("1. Звичайний квиток (Standard)")
        print("2. ВІП-квиток (VIP)")
        print("3. Студентський квиток (Student)")
        print("4. Повернутися до головного меню")

        choice = input("Оберіть опцію (1-4): ").strip()
        if choice == "4":
            return
        if choice not in ("1", "2", "3"):
            print("[ПОМИЛКА] Невірний вибір. Будь ласка, введіть число від 1 до 4.")
            continue

        manager.add_ticket(create_ticket(choice, movie))
        if not ask_yes("\nБажаєте замовити ще квиток? (так/ні): "):
            print("\nДякуємо за покупку! Приємного перегляду 🍿🎬")
            return

# --- Блок демонстрації (Main CLI) ---
if __name__ == "__main__":
    print("--- Cinema System CLI: Система управління кінотеатром ---")
    manager = CinemaManager()
    current_movie = None

    while True:
        print("\n" + "=" * 40)
        print("ГОЛОВНЕ МЕНЮ".center(40))
        print("=" * 40)
        print("1. Замовити квиток (Гілка клієнта)")
        print("2. Переглянути архів (Тільки для менеджера)")
        print("3. Вихід з програми")

        main_choice = input("Оберіть дію (1-3): ").strip()

        try:
            if main_choice == "1":
                if current_movie is None:
                    current_movie = create_movie()
                ticket_menu(current_movie, manager)
            elif main_choice == "2":
                manager.show_all_tickets()
            elif main_choice == "3":
                print("\nРоботу системи завершено. До зустрічі! 👋")
                break
            else:
                print("[ПОМИЛКА] Невірний вибір. Будь ласка, введіть число від 1 до 3.")
        except ValueError as e:
            print(f"\n[ПОМИЛКА ВАЛІДАЦІЇ] {e}")
        except Exception as e:
            print(f"\n[ПОМИЛКА] Виникла непередбачувана ситуація: {e}")