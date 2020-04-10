class A:
    def __init__(self):
        self.var = False

    def __str__(self):
        return str(self.var)



a1 = A()
a2 = A()
a3 = A()
a4 = A()

li = []
li.append(a1)
li.append(a2)
li.append(a3)
li.append(a4)

a2.var = True
a3.var = True

print(li)
li[:] = [x for x in li if not x.var]
print(li)