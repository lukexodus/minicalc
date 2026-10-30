# 05_errors.mc — Demonstrates all 8 MiniCalc error classes
# Each line triggers a distinct error family; execution continues across errors.

# 1. LexError: non-integer float literal
3.14

# 2. ParseError: invalid syntax with consecutive operators
2 + * 3

# 3. DivisionByZeroError: division by zero
10 / 0

# 4. IntegerRangeError: 32-bit signed integer overflow
2147483647 + 1

# 5. DomainError: negative exponent
2 ** -1

# 6. UndefinedNameError: variable accessed before assignment
unknown_var + 1

# 7. CallError: invocation of unknown function
foo(1)

# 8. AssignmentError: assignment to reserved identifier ans
ans = 42
