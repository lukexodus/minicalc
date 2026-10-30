# 03_variables.mc — Variables, assignment, and ans

# Variable assignment: name = expression
width = 20
height = 5

# Using variables in expressions
area = width * height
perimeter = 2 * (width + height)

# ans holds the value of the most recent successful expression
area + 10

# Reading ans in an expression
ans * 2

# Assignments do not update ans; ans still refers to the previous expression result
scale = 3
ans
