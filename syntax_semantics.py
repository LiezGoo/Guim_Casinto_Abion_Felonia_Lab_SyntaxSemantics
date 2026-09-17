class ParserError(Exception):
	"""An error raised when an expression does not match the grammar."""

	def __init__(self, position, reason):
		self.position = position
		self.reason = reason
		super().__init__(reason)


class Parser:
	def __init__(self, text):
		self.text = text
		self.position = 0

	def skip_spaces(self):
		while self.position < len(self.text) and self.text[self.position].isspace():
			self.position += 1

	def current_token(self):
		self.skip_spaces()
		if self.position >= len(self.text):
			return None
		return self.text[self.position]

	def consume(self, expected=None):
		token = self.current_token()
		if token is None:
			raise ParserError(self.position, "unexpected end of input")
		if expected is not None and token != expected:
			raise ParserError(
				self.position,
				f"expected '{expected}', found '{token}'",
			)
		self.position += 1
		return token

	# <expr> -> <term> { (+ | -) <term> }
	def parse_expr(self):
		value = self.parse_term()

		while self.current_token() in ("+", "-"):
			operator = self.consume()
			right = self.parse_term()
			if operator == "+":
				value += right
			else:
				value -= right

		return value

	# <term> -> <factor> { (* | /) <factor> }
	def parse_term(self):
		value = self.parse_factor()

		while self.current_token() in ("*", "/"):
			operator = self.consume()
			right = self.parse_factor()
			if operator == "*":
				value *= right
			else:
				if right == 0:
					raise ParserError(self.position, "division by zero")
				value /= right

		return value

	# <factor> -> ( <expr> ) | <digit>
	def parse_factor(self):
		token = self.current_token()

		if token is None:
			raise ParserError(self.position, "expected a digit or '('")

		if token.isdigit() and token in "0123456789":
			self.consume()
			return int(token)

		if token == "(":
			self.consume("(")

			# Recursive step corresponding to <factor> -> ( <expr> ).
			value = self.parse_expr()

			if self.current_token() != ")":
				raise ParserError(self.position, "missing closing parenthesis ')'" )
			self.consume(")")
			return value

		raise ParserError(self.position, f"unexpected token '{token}'")

	def parse(self):
		self.skip_spaces()
		if self.current_token() is None:
			raise ParserError(self.position, "input is empty")

		value = self.parse_expr()
		leftover = self.current_token()
		if leftover is not None:
			raise ParserError(self.position, f"unexpected token '{leftover}'")
		return int(value) if value == int(value) else value


def evaluate_expression(expression):
	"""Parse and evaluate one expression, returning its numeric value."""
	return Parser(expression).parse()


def naive_left_to_right_evaluation(expression):
	"""Demonstrate evaluation without normal operator precedence.

	This small demonstration accepts digits and the four arithmetic operators.
	It intentionally evaluates each operation as soon as the next number is
	read, so 2+3*4 becomes (2+3)*4.
	"""
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


def main():
	demonstrate_ambiguity()
	run_required_tests()

	while True:
		expression = input("Enter expression: ")
		if expression.strip().lower() in ("quit", "exit"):
			print("Goodbye.")
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
