class BMI_Calculator:
   
    def __init__(self, weight: float, height: float):
        self.weight = weight
        self.height = height

    # Робота з вагою (weight)
    @property
    def weight(self) -> float:
        return self.__weight

    @weight.setter
    def weight(self, value: float):
        if value <= 0:
            raise ValueError("Вага повинна бути більшою за нуль.")
        self.__weight = value

    # Робота зі зростом (height)
    @property
    def height(self) -> float:
        return self.__height

    @height.setter
    def height(self, value: float):
        if value <= 0:
            raise ValueError("Зріст повинен бути більшим за нуль.")
        self.__height = value

    # Основна логіка
    def calculate_bmi(self) -> float:
        return self.__weight / (self.__height ** 2)

    def __str__(self) -> str:
        return f"BMI_Calculator(вага={self.weight} кг, зріст={self.height} м)"


# Блок демонстрації (Main)
if __name__ == "__main__":
    print("------Програма розрахунку індексу маси тіла (ІМТ)------")
    
    try:
        # 1. Отримання даних від користувача
        user_weight = float(input("Введіть вашу вагу в кг: "))
        user_height = float(input("Введіть ваш зріст у метрах: "))

        # 2. Створення екземпляру класу
        calculator = BMI_Calculator(user_weight, user_height)

        # 3. Вивід інформації та результату
        print(f"\nОб'єкт створено: {calculator}")
        print(f"Ваш індекс маси тіла (ІМТ): {calculator.calculate_bmi():.2f}")


    except ValueError as e:
        # Перехоплення помилок валідації
        print(f"\nПомилка: {e}")
    except Exception as e:
        # Перехоплення будь-яких інших непередбачуваних помилок
        print(f"\nВиникла непередбачувана помилка: {e}")