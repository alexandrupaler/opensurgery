'''
to use this:
pip install openfermioncirq
'''
import cirq

class CirqInterface:
    def __init__(self):
        c = cirq.Circuit()

        q = cirq.NamedQubit("q")

        c.append(cirq.X(q))

        print(c.to_qasm())



