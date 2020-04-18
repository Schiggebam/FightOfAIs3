import os



class A:
    def __init__(self, b):
        self.b:B = b
        self.value = 10

    def a(self):
        self.b.b(self)


class B:
    def b(self, a: A):
        print(a.value)


bb = B()
aa = A(bb)
aa.a()


print(os.getcwd())

def fun_1(amount, index_fun):
    for i in range(amount):
        print(index_fun(i))



f = lambda i: (0, 100*i)
fun_1(10, f)