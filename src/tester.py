import os


print(os.getcwd())

def fun_1(amount, index_fun):
    for i in range(amount):
        print(index_fun(i))



f = lambda i: (0, 100*i)
fun_1(10, f)