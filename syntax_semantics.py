class ParserError(Exception):
	"""An error raised when an expression does not match the grammar."""

	def __init__(self, position, reason):
		# Where in the string things went wrong...
		self.position = position
		# ...and why, in plain English.
		self.reason = reason
		super().__init__(reason)


class Parser:
	def __init__(self, text):
		self.text = text       # the raw string we're reading, e.g. "3+4*2"
		self.position = 0      # index of the NEXT character we haven't looked at yet

	def skip_spaces(self):
		# Move position forward past any whitespace, so "3 + 4" reads the
		# same as "3+4". Doesn't return anything - just adjusts self.position.
		while self.position < len(self.text) and self.text[self.position].isspace():
			self.position += 1

	def current_token(self):
		# "Peek" at the next character WITHOUT consuming it - like looking
		# at the top card of a deck without picking it up.
		self.skip_spaces()
		if self.position >= len(self.text):
			return None  # nothing left to read
		return self.text[self.position]

	def consume(self, expected=None):
		# Actually "pick up" the next character and move position forward.
		# If `expected` is given, first check the character matches - this
		# is how we enforce things like "there MUST be a ')' here".
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
	# In plain words: "an expr is one term, optionally followed by any
	# number of (+ or -) and another term".
	def parse_expr(self):
		# Step 1: get the first term. E.g. in "3+4*2", this call alone
		# handles the "3" (parse_term will dig further down for "4*2").
		value = self.parse_term()

		# Step 2: keep absorbing + / - as long as we see them.
		# This loop is what makes + and - LEFT-associative:
		# "1-2-3" is read as (1-2)-3, not 1-(2-3), because we always
		# apply the operator we just saw to the running total `value`.
		while self.current_token() in ("+", "-"):
			operator = self.consume()          # eat the '+' or '-'
			right = self.parse_term()          # get the next term (may itself involve * or /)
			if operator == "+":
				value += right
			else:
				value -= right

		return value  # the final running total is the meaning of this <expr>

	# <term> -> <factor> { (* | /) <factor> }
	# Same shape as parse_expr, but one level down: factors joined by * or /.
	# Because parse_expr calls parse_term (not the other way around),
	# all the *'s and /'s here get fully resolved BEFORE parse_expr ever
	# gets a chance to add or subtract anything. That's the whole trick
	# behind precedence - no special "check precedence" logic needed.
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
				value /= right   # true division here; cleaned up to an int later in parse()

		return value

	# <factor> -> ( <expr> ) | <digit>
	# The "bottom" of the hierarchy: either a single digit, or a fully
	# parenthesized expression treated as one unit.
	def parse_factor(self):
		token = self.current_token()

		if token is None:
			raise ParserError(self.position, "expected a digit or '('")

		# Case 1: a plain digit, e.g. the "3" in "3+4".
		if token.isdigit() and token in "0123456789":
			self.consume()
			return int(token)

		# Case 2: an opening parenthesis - here's the recursion.
		if token == "(":
			self.consume("(")

			# THE RECURSIVE STEP: to know the value of "(...)", we need to
			# parse a WHOLE expression again, starting from scratch - so
			# we call parse_expr(), the same method three levels up.
			# This is how "(3+4)*2" works: everything inside the parens
			# is fully resolved into one number (7) via this nested call,
			# and parse_term (the caller of parse_factor) just sees "7"
			# and multiplies it by 2, with no idea parens were involved.
			value = self.parse_expr()

			# After the inner expression is done, the very next character
			# MUST be a closing paren, or the input is malformed
			# (e.g. "(3+4" with no ")").
			if self.current_token() != ")":
				raise ParserError(self.position, "missing closing parenthesis ')'")
			self.consume(")")
			return value

		# Neither a digit nor '(' - the input doesn't match the grammar here.
		raise ParserError(self.position, f"unexpected token '{token}'")

	def parse(self):
		# This is the single entry point everything else should call.
		self.skip_spaces()
		if self.current_token() is None:
			raise ParserError(self.position, "input is empty")

		# Parse the whole thing top-down, starting at the loosest level.
		value = self.parse_expr()

		# If parse_expr() finished but characters remain (e.g. a stray
		# ')' with no matching '(', like "3+4)"), that's still invalid -
		# a valid expression must consume the ENTIRE string.
		leftover = self.current_token()
		if leftover is not None:
			raise ParserError(self.position, f"unexpected token '{leftover}'")

		# Division above always produces a float in Python (8/2 -> 4.0).
		# If the value happens to be a whole number, hand back a clean
		# int instead of e.g. 3.0, so results print as "3" not "3.0".
		return int(value) if value == int(value) else value


def evaluate_expression(expression):
	"""Parse and evaluate one expression, returning its numeric value."""
	return Parser(expression).parse()


def naive_left_to_right_evaluation(expression):
	"""Demonstrate evaluation without normal operator precedence.

	This deliberately IGNORES precedence and just applies operators in
	the order they're read, left to right - showing what would happen
	if the grammar didn't distinguish <term> from <expr>. For "2+3*4"
	this computes (2+3)*4 = 20, instead of the correct 2+(3*4) = 14.
	"""
	# Strip spaces, e.g. "2 + 3" -> ['2','+','3']
	characters = [character for character in expression if not character.isspace()]
	if not characters or not characters[0].isdigit():
		raise ValueError("the demonstration expression must start with a digit")

	value = int(characters[0])   # start with the first number
	index = 1
	while index < len(characters):
		operator = characters[index]
		if operator not in "+-*/" or index + 1 >= len(characters):
			raise ValueError("invalid demonstration expression")
		right = int(characters[index + 1])
		# Apply the operator to the running total IMMEDIATELY - no
		# waiting to see if a higher-precedence operator comes later.
		# This is exactly why 2+3*4 becomes (2+3)*4 here.
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
		index += 2  # move past this operator AND the number after it
	return int(value) if value == int(value) else value


def demonstrate_ambiguity():
	# Side-by-side comparison: the "wrong" naive answer vs. the "right"
	# grammar-based answer, for the same input string.
	expression = "2+3*4"
	print("=== Ambiguity Demonstration ===")
	print(f"Expression: {expression}")
	print(
		"Left-to-right evaluation: "
		f"{naive_left_to_right_evaluation(expression)}"
	)
	print(f"Precedence-based evaluation: {evaluate_expression(expression)}")
	# The written explanation the rubric asks for: WHY the corrected
	# grammar (with <term> underneath <expr>) can't produce this
	# ambiguity, unlike the flat grammar that treats + and * as equals.
	print("The unfixed grammar (<expr> -> <expr> + <expr> | <expr> * <expr> | <digit>) gives '+' and '*' equal status, so '2+3*4' has two legal parse trees. The corrected grammar removes the ambiguity by placing <term> below <expr> in the hierarchy, forcing '*'/'/' to bind to their neighboring <factor>s before any '+'/'-' at the <expr> level applies, and making the left-to-right repetition at each level give left-associativity, so there's exactly one parse tree per string.")
	print()


def run_required_tests():
	# Each tuple: (input string, should it be valid?, expected value if valid)
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
			# Reached here only if parsing succeeded - check it also got
			# the value the assignment expects.
			status = "Valid" if should_be_valid and result == expected else "UNEXPECTED"
			print(f"{expression:10} -> {status} -> {result}")
		except ParserError:
			# Reached here if parsing failed - that's correct only if
			# this test case was SUPPOSED to be invalid.
			status = "Invalid" if not should_be_valid else "UNEXPECTED"
			print(f"{expression:10} -> {status}")
	print()


def main():
	# Run the two required demonstrations first...
	demonstrate_ambiguity()
	run_required_tests()

	# ...then let a human type in their own expressions interactively,
	# printing the syntax verdict and (if valid) the computed value,
	# matching the "Invalid syntax" / position format the assignment asks for.
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