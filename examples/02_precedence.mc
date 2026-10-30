# 02_precedence.mc — Operator precedence and associativity

# Multiplication binds tighter than addition
2 + 3 * 4

# Parentheses override default precedence
(2 + 3) * 4

# Left-associative subtraction and division
20 - 5 - 3
100 / 5 / 2

# Exponentiation (**) binds tighter than unary minus: -2 ** 2 is -(2 ** 2)
-2 ** 2

# Exponentiation is right-associative: 2 ** 3 ** 2 is 2 ** (3 ** 2) = 2 ** 9
2 ** 3 ** 2

# Arithmetic binds tighter than comparison
2 + 3 == 5
10 * 2 > 15

# Comparisons return 1 (true) or 0 (false)
5 >= 5
4 != 4
