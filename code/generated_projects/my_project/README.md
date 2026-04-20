# Simple Calculator Project
## Overview
This project is a simple command-line calculator built in Python. It provides basic arithmetic operations like addition, subtraction, multiplication, and division.
## Usage
1. Run the `main.py` file using Python (e.g., `python main.py`).
2. Choose an operation by entering the corresponding number (1 for addition, 2 for subtraction, 3 for multiplication, 4 for division).
3. Enter two numbers when prompted.
4. The calculator will display the result of the chosen operation.
## Calculator Class
The `Calculator` class contains methods for each arithmetic operation:
* `add(num1: float, num2: float) -> float`: Returns the sum of two numbers.
* `subtract(num1: float, num2: float) -> float`: Returns the difference between two numbers.
* `multiply(num1: float, num2: float) -> float`: Returns the product of two numbers.
* `divide(num1: float, num2: float) -> float`: Returns the quotient of two numbers, handling division by zero.
## Error Handling
The calculator includes input validation to ensure that users enter numbers. It also handles division by zero by raising a `ZeroDivisionError`.
## Notes
This project demonstrates a simple, object-oriented design pattern and provides a clean command-line interface for user interaction.