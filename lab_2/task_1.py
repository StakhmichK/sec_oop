from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid

# 1. Перелічуваний тип (Enum) для статусу квитка
class TicketStatus(Enum):
    BOOKED = "Заброньовано"
    PAID = "Оплачено"
    CANCELLED = "Скасовано"


# 2. Використання dataclass для збереження даних про фільм
@dataclass
class Movie:
    """Клас для зберігання інформації про фільм."""
    title: str
    genre: str
    duration_min: int 
# 3. Поведінковий клас з інкапсуляцією та валідацією
class Ticket:
    """Клас для квитка в кіно з валідацією ціни та місця."""
    def __init__(self, movie: Movie, price: float, seat: str, status: TicketStatus = TicketStatus.BOOKED):
        self.id = str(uuid.uuid4())[:8]
        self.movie = movie
        self.status = status
        self.created_at = datetime.now()
        
        # Передаємо через властивості (properties) для автоматичної валідації в сетерах
        self.seat = seat
        self.price = price

    # --- Робота з ціною (price) ---
    @property
    def price(self) -> float:
        """Гетер для отримання ціни квитка."""
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        """Сетер для встановлення ціни з перевіркою коректності даних."""
        if not isinstance(value, (int, float)):
            raise ValueError("Ціна квитка повинна бути числом!")
        if value <= 0:
            raise ValueError("Ціна квитка повинна бути більшою за 0 грн!")
        self._price = float(value)

    # --- Робота з номером місця (seat) ---
    @property
    def seat(self) -> str:
        """Гетер для отримання номера місця."""
        return self._seat

    @seat.setter
    def seat(self, value: str) -> None:
        """Сетер із валідацією формату місця в залі."""
        if not isinstance(value, str) or len(value.strip()) < 2:
            raise ValueError("Номер місця має містити щонайменше 2 символи (наприклад, 'A-12')!")
        self._seat = value.strip().upper()


# --- Блок демонстрації (Main CLI) ---
if __name__ == "__main__":
    print("--- Cinema System CLI: Система управління кінотеатром ---")

    try:
        # Повний ввід даних від користувача
        print("\n=== Введення даних про фільм ===")
        movie_title = input("Введіть назву фільму: ")
        movie_genre = input("Введіть жанр фільму: ")
        raw_duration_input = input("Введіть тривалість фільму (хв): ")
        
        # Валідація тривалості фільму
        try:
            movie_duration = int(raw_duration_input)
            if movie_duration <= 0:
                raise ValueError("Тривалість фільму повинна бути більшою за 0 хвилин!")
        except ValueError as err:
            if "invalid literal" in str(err):
                raise ValueError("Тривалість фільму повинна бути цілим числом!")
            raise err

        print("\n=== Введення даних про квиток ===")
        seat_input = input("Введіть номер ряду та місця (наприклад, A-12): ")
        raw_price_input = input("Введіть ціну квитка (грн): ")

        # Спроба перетворення ціни на число (або передача рядка для спрацювання сетера)
        try:
            raw_price = float(raw_price_input)
        except ValueError:
            raw_price = raw_price_input

        # Динамічне створення об'єкта Movie на основі введених даних
        user_movie = Movie(
            title=movie_title.strip(),
            genre=movie_genre.strip(),
            duration_min=movie_duration
        )

        # Створення об'єкта квитка
        my_ticket = Ticket(
            movie=user_movie,
            price=raw_price,
            seat=seat_input,
            status=TicketStatus.PAID
        )

        # Успішний вивід
        print("\n[УСПІХ] Квиток успішно створено:")
        print(f"ID об'єкта в пам'яті: {id(my_ticket)}")
        print(f"Код квитка: {my_ticket.id}")
        print(f"Фільм: {my_ticket.movie.title} ({my_ticket.movie.genre}, {my_ticket.movie.duration_min} хв)")
        print(f"Місце: {my_ticket.seat}")
        print(f"Статус: {my_ticket.status.value}")
        print(f"Ціна: {my_ticket.price:.2f} грн")
        print(f"Дата створення: {my_ticket.created_at.strftime('%Y-%m-%d %H:%M')}")

        # Інспекція внутрішнього стану об'єкта
        print("\n--- Інспекція внутрішнього стану (vars) ---")
        print(vars(my_ticket))

    except ValueError as e:
        # Перехоплення помилок валідації із сетерів та вводу
        print(f"\n[ПОМИЛКА ВАЛІДАЦІЇ] {e}")
    except Exception as e:
        print(f"\n[ПОМИЛКА] Виникла непередбачувана ситуація: {e}")