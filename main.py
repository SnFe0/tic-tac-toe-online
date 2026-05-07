from functools import lru_cache

@lru_cache(None)
def f(a,b):
    if a > b:
        return 0
    elif a == b:
        return 1
    elif a % 2 == 0:
        return f(a+1, b) + f(a*1.5, b)
    return f(a+1, b)

print(f(1, 20))