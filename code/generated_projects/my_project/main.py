import sys

class Calculator:
    def add(self, num1: float, num2: float) -> float:
        """
        Returns the sum of two numbers.
        """
        return num1 + num2

    def subtract(self, num1: float, num2: float) -> float:
        """
        Returns the difference between two numbers.
        """
        return num1 - num2

    def multiply(self, num1: float, num2: float) -> float:
        """
        Returns the product of two numbers.
        """
        return num1 * num2

    def divide(self, num1: float, num2: float) -> float:
        """
        Returns the quotient of two numbers, handling division by zero.
        """
        if num2 == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return num1 / num2


def get_user_input() -> tuple:
    """
    Prompts the user to enter two numbers and validates the input.
    """
    while True:
        try:
            num1 = float(input("Enter the first number: "))
            num2 = float(input("Enter the second number: "))
            return num1, num2
        except ValueError:
            print("Invalid input. Please enter a number.")


def display_result(result: float) -> None:
    """
    Displays the calculation result to the user.
    """
    print(f"Result: {result}")


def main() -> None:
    calculator = Calculator()
    print("Simple Calculator")
    print("1. Addition")
    print("2. Subtraction")
    print("3. Multiplication")
    print("4. Division")
    choice = input("Choose an operation (1/2/3/4): ")
    num1, num2 = get_user_input()
    if choice == '1':
        result = calculator.add(num1, num2)
    elif choice == '2':
        result = calculator.subtract(num1, num2)
    elif choice == '3':
        result = calculator.multiply(num1, num2)
    elif choice == '4':
        try:
            result = calculator.divide(num1, num2)
        except ZeroDivisionError as e:
            print(str(e))
            return
    else:
        print("Invalid choice.")
        return
    display_result(result)

if __name__ == '__main__':
    main()
