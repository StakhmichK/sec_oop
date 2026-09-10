class ProbabilityCalculator:
    """
    Клас для розрахунку ймовірності успіху події.
    Демонструє підхід до інкапсуляції через властивості (properties).
    """

    def __init__(self, success_events: int, total_events: int):
        # Порядок важливий! Спочатку задаємо загальну кількість, 
        # щоб сетер success_events міг перевірити, чи не перевищує він total_events.
        self.total_events = total_events
        self.success_events = success_events

    # --- Робота із загальною кількістю подій (total_events) ---

    @property
    def total_events(self) -> int:
        """Гетер для отримання загальної кількості подій."""
        return self.__total_events

    @total_events.setter
    def total_events(self, value: int):
        """Сетер для встановлення загальної кількості подій з валідацією (>0)."""
        if value <= 0:
            raise ValueError("Загальна кількість подій повинна бути більшою за нуль!")
        
        # Якщо успішні події вже були встановлені раніше, перевіряємо, 
        # щоб нова загальна кількість не стала меншою за кількість успіхів
        if hasattr(self, '_ProbabilityCalculator__success_events') and value < self.__success_events:
            raise ValueError("Загальна кількість подій не може бути меншою за кількість вже встановлених успіхів!")
            
        self.__total_events = value

    # --- Робота з кількістю успішних подій (success_events) ---

    @property
    def success_events(self) -> int:
        """Гетер для отримання кількості успішних подій."""
        return self.__success_events

    @success_events.setter
    def success_events(self, value: int):
        """Сетер для встановлення кількості успіхів з валідацією (>0 та <= total_events)."""
        if value <= 0:
            raise ValueError("Кількість успішних подій повинна бути більшою за нуль!")
        
        # Перевіряємо, щоб успіхи не перевищували загальну кількість
        if hasattr(self, '_ProbabilityCalculator__total_events') and value > self.__total_events:
            raise ValueError("Кількість успіхів не може перевищувати загальну кількість подій!")
            
        self.__success_events = value

    # --- Основна логіка ---

    def calculate_probability(self) -> float:
        """Метод для розрахунку ймовірності (від 0 до 1)."""
        return self.__success_events / self.__total_events

    def __str__(self) -> str:
        """Текстове представлення об'єкта."""
        return f"ProbabilityCalculator(успіхи={self.success_events}, всього={self.total_events})"


# --- Блок демонстрації (Main) ---

if __name__ == "__main__":
    print("--- Програма розрахунку ймовірності події ---")
    
    try:
        # 1. Отримання даних від користувача (використовуємо int, оскільки події цілі числа)
        user_total = int(input("Введіть загальну кількість подій: "))
        user_success = int(input("Введіть кількість успішних подій: "))

        # 2. Створення екземпляру класу
        calc = ProbabilityCalculator(success_events=user_success, total_events=user_total)

        # 3. Вивід інформації та результату
        print(f"\nОб'єкт створено: {calc}")
        print(f"Ймовірність успіху: {calc.calculate_probability():.4f}")

    except ValueError as e:
        # Перехоплення помилок валідації та некоректного введення
        print(f"\nПомилка: {e}")
    except Exception as e:
        # Перехоплення інших помилок
        print(f"\nВиникла непередбачувана помилка: {e}")