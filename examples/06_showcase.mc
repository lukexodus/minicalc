# 06_showcase.mc — Realistic computations in MiniCalc
# Covers compound interest in whole pesos, GCD fraction reduction, and bit-size calculations.

# -----------------------------------------------------------------------------
# 1. Compound Interest in Whole Pesos
# Grow a 50,000 PHP investment at 8% per year over a 3-year term
# -----------------------------------------------------------------------------
principal = 50000
rate = 8

# Year 1 balance
year1 = principal + (principal * rate) / 100

# Year 2 balance
year2 = year1 + (year1 * rate) / 100

# Year 3 balance
year3 = year2 + (year2 * rate) / 100

# Total interest earned across the full 3-year term
total_interest = year3 - principal

# -----------------------------------------------------------------------------
# 2. GCD Fraction Reduction
# Reduce fraction 840 / 1260 to its simplest irreducible terms
# -----------------------------------------------------------------------------
numerator = 840
denominator = 1260

common_factor = gcd(numerator, denominator)
reduced_num = numerator / common_factor
reduced_den = denominator / common_factor

# -----------------------------------------------------------------------------
# 3. Bit-size and Address Space Calculation
# Calculate addressable bytes and maximum memory range using powers of 2
# -----------------------------------------------------------------------------
# Total bytes addressable by a 24-bit address bus (16 MiB)
bus_bits = 24
addressable_bytes = 2 ** bus_bits
addressable_kib = addressable_bytes / 1024
addressable_mib = addressable_kib / 1024

# Highest positive value representable in signed 32-bit integers (2^31 - 1)
int_max = (2 ** 30 - 1) + 2 ** 30
