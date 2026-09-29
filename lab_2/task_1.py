from dataclasses import dataclass
from datetime import datetime
import uuid

# 1. Використання dataclass для збереження даних про фільм
@dataclass
class Movie:
    title: str
    genre: str
    duration_min: int


# 2. Поведінковий клас з інкапсуляцією та валідацією
class Ticket:
    def __init__(self, movie: Movie, price: float):
        self.id = str(uuid.uuid4())[:8]
        self.movie = movie
        # Викликаємо сетер для валідації початкового значення ціни
        self.price = price

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Ціна квитка повинна бути числом!")
        if value <= 0:
            raise ValueError("Ціна квитка повинна бути більшою за 0!")
        self._price = float(value)


# --- Блок демонстрації (Main) ---
if __name__ == "__main__":
    print("=== Система управління кінотеатром: Створення квитка ===")

    try:
        # Отримання даних від користувача
        movie_title = input("Введіть назву фільму: ")
        movie_genre = input("Введіть жанр фільму: ")
        raw_price = float(input("Введіть ціну квитка (грн): "))

        # Створення екземплярів класів
        movie = Movie(title=movie_title, genre=movie_genre, duration_min=120)
        ticket = Ticket(movie=movie, price=raw_price)

        # Вивід успішно створеного квитка
        print(f"\nКвиток [{ticket.id}] успішно створено!")
        print(f"Фільм: {ticket.movie.title} ({ticket.movie.genre})")
        print(f"Ціна: {ticket.price:.2f} грн")

    except ValueError as e:
        print(f"Помилка валідації даних: {e}")
    except Exception as e:
        print(f"Виникла непередбачувана помилка: {e}")