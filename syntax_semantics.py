# Parse Error
class ParserError(Exception):
    def __init__(self, position, reason):
        # Store both pieces so the interactive program can report useful
        # syntax diagnostics instead of only saying that parsing failed.
        self.position = position
        self.reason = reason
        super().__init__(reason)

# Parser class and token operations

class Parser:
    """Read, validate, and evaluate an arithmetic expression."""

    def __init__(self, text):
        self.text = text
        # position points to the next character that has not been consumed.
        self.position = 0

    def skip_spaces(self):
        """Advance past whitespace so spacing does not affect the grammar."""
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.position += 1

    def current_token(self):
        """Read, or peek at, the next token without consuming it."""
        self.skip_spaces()
        if self.position >= len(self.text):
            return None
        return self.text[self.position]

    def consume(self, expected=None):
        """Consume the next token, optionally requiring a specific token."""
        token = self.current_token()
        if token is None:
            raise ParserError(self.position, "unexpected end of input")
        if expected is not None and token != expected:
            # Checking before advancing preserves the position of the error.
            raise ParserError(
                self.position,
                f"expected '{expected}', found '{token}'",
            )
        self.position += 1
        return token
    # Grammar parsing functions


    # Grammar rule:
    # <expr> -> <term> { (+ | -) <term> }
    def parse_expr(self):
        """Parse and evaluate an expression made from terms and + or -."""
        # Calling parse_term first gives multiplication and division priority.
        value = self.parse_term()

        # Repeating this loop implements { (+ | -) <term> } and permits chains.
        # Updating the running value makes + and - left-associative: 1-2-3
        # becomes (1-2)-3 rather than 1-(2-3).
        while self.current_token() in ("+", "-"):
            operator = self.consume()  # Consume the operator just read.
            right = self.parse_term()  # Parse the following complete term.
            if operator == "+":
                value += right
            else:
                value -= right

        return value

    # Grammar rule:
    # <term> -> <factor> { (* | /) <factor> }
    def parse_term(self):
        """Parse and evaluate a term made from factors and * or /."""
        # The call chain is <expr> -> <term> -> <factor>; this hierarchy is
        # what achieves precedence without adding separate precedence logic.
        value = self.parse_factor()

        # This loop handles * and / before parse_expr handles + and -.
        # Applying each operator to the running value makes them left-
        # associative too: 8/2*3 becomes (8/2)*3.
        while self.current_token() in ("*", "/"):
            operator = self.consume()  # Consume the operator just read.
            right = self.parse_factor()  # Parse the following factor.
            if operator == "*":
                value *= right
            else:
                if right == 0:
                    raise ParserError(self.position, "division by zero")
                value /= right

        return value

    # Grammar rule:
    # <factor> -> ( <expr> ) | <digit>
    def parse_factor(self):
        """Parse one digit or one parenthesized expression."""
        token = self.current_token()  # Read the next token without consuming it.

        if token is None:
            raise ParserError(self.position, "expected a digit or '('")

        # A digit is the base case of the grammar, so it needs no recursion.
        if token.isdigit() and token in "0123456789":
            self.consume()
            return int(token)

        if token == "(":
            self.consume("(")  # Consume '(' before parsing its contents.

            # Recursive step:
            # <factor> -> ( <expr> )
            # parse_factor() calls parse_expr() to parse the expression
            # inside the parentheses.
            value = self.parse_expr()

            # The closing ')' is required to complete the grammar alternative.
            if self.current_token() != ")":
                raise ParserError(self.position, "missing closing parenthesis ')'")
            self.consume(")")
            return value

        # Any other token cannot begin a factor, so report the exact position.
        raise ParserError(self.position, f"unexpected token '{token}'")

    # Grammar entry point:
    # <expr> is the complete input according to the grammar above.
    def parse(self):
        """Parse the complete input and return its calculated value."""
        self.skip_spaces()
        if self.current_token() is None:
            raise ParserError(self.position, "input is empty")

        # Start at the highest grammar level and let the calls descend through
        # <expr> -> <term> -> <factor>, which establishes operator precedence.
        value = self.parse_expr()

        # A successful expression must consume the entire input; otherwise a
        # leftover token such as ')' would be silently accepted as valid.
        leftover = self.current_token()
        if leftover is not None:
            raise ParserError(self.position, f"unexpected token '{leftover}'")

        # Division produces floats, but whole-number results are displayed as
        # integers to preserve the program's existing output format.
        return int(value) if value == int(value) else value

# Evaluation functions

def evaluate_expression(expression):
    """Parse and evaluate one expression, returning its numeric value."""
    return Parser(expression).parse()


def naive_left_to_right_evaluation(expression):
    """Demonstrate evaluation without the grammar's operator precedence."""
    # Removing spaces lets this deliberately simple demonstration inspect one
    # digit and one operator at a time, without changing the parser itself.
    characters = [character for character in expression if not character.isspace()]
    if not characters or not characters[0].isdigit():
        raise ValueError("the demonstration expression must start with a digit")

    value = int(characters[0])
    index = 1
    while index < len(characters):
        operator = characters[index]
        if operator not in "+-*/" or index + 1 >= len(characters):
            raise ValueError("invalid demonstration expression")
        right = int(characters[index + 1])

        # Applying each operator immediately ignores the <expr>/<term>
        # hierarchy, so 2+3*4 becomes (2+3)*4 and produces 20.
        if operator == "+":
            value += right
        elif operator == "-":
            value -= right
        elif operator == "*":
            value *= right
        else:
            if right == 0:
                raise ValueError("division by zero")
            value /= right
        index += 2

    return int(value) if value == int(value) else value

# Ambiguity demonstration

def demonstrate_ambiguity():
    expression = "2+3*4"
    print("=== Ambiguity Demonstration ===")
    print(f"Expression: {expression}")
    print(
        "Left-to-right evaluation: "
        f"{naive_left_to_right_evaluation(expression)}"
    )
    print(f"Precedence-based evaluation: {evaluate_expression(expression)}")
    print("The unfixed grammar (<expr> -> <expr> + <expr> | <expr> * <expr> | <digit>) gives '+' and '*' equal status, so '2+3*4' has two legal parse trees. The corrected grammar removes the ambiguity by placing <term> below <expr> in the hierarchy, forcing '*'/'/' to bind to their neighboring <factor>s before any '+'/'-' at the <expr> level applies, and making the left-to-right repetition at each level give left-associativity, so there's exactly one parse tree per string.")
    print()

# Required test cases

def run_required_tests():
    test_cases = [
        ("3+4*2", True, 11),
        ("(3+4)*2", True, 14),
        ("8/2-1", True, 3),
        ("3++4", False, None),
        ("(3+4", False, None),
        ("2+3*4", True, 14),
    ]

    print("=== Required Test Cases ===")
    for expression, should_be_valid, expected in test_cases:
        try:
            result = evaluate_expression(expression)
            status = "Valid" if should_be_valid and result == expected else "UNEXPECTED"
            print(f"{expression:10} -> {status} -> {result}")
        except ParserError:
            status = "Invalid" if not should_be_valid else "UNEXPECTED"
            print(f"{expression:10} -> {status}")
    print()

# Main program

def main():
    demonstrate_ambiguity()
    run_required_tests()

    while True:
        expression = input("Enter expression: ")
        if expression.strip().lower() in ("quit", "exit"):
            print("Program finished.")
            break

        try:
            result = evaluate_expression(expression)
            print("Valid syntax")
            print(f"Result: {result}")
        except ParserError as error:
            print("Invalid syntax")
            print(f"Error at position {error.position}: {error.reason}")


if __name__ == "__main__":
    main()