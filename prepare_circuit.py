'''
Decompose a list of strings into another list of strings.
This will be very similar to how the javascript tool works
'''


class PrepareCircuit:
    def __init__(self):
        print("Prepare Circuit")

    def parse_to_my_string_format(self, cirq_circuit):
        # the first 5 lines are header
        str_s = [s for s in cirq_circuit.to_qasm().split("\n") if s.strip() != ''][4:]

        str_s = [s.replace("h", "H") for s in str_s]
        str_s = [s.replace("rz(pi*0.25)", "T") for s in str_s]
        str_s = [s.replace("rz(pi*0.5)", "S") for s in str_s]
        str_s = [s.replace("cx", "CNOT") for s in str_s]

        str_s = [s.replace("q[", "")
                     .replace("]", "")
                     .replace(",", " ")
                     .replace(";", "")
                     .strip() for s in str_s]

        return str_s

    def replace_gates_with_multibody(self, gate_list):
        ret_list = []
        for gate in gate_list:
            qub = gate.split(" ")[-1]
            if gate.startswith("T"):
                ret_list.append("NEED A")
                ret_list.append("MZZ A " + qub)
                ret_list.append("MX A")
            elif gate.startswith("S"):
                ret_list.append(gate)
            elif gate.startswith("H"):
                ret_list.append(gate)
                ret_list.append("ROTATE " + qub)
            elif gate.startswith("CNOT"):
                qub_control = gate.split(" ")[-2]
                ret_list.append("ANCILLA 0")
                ret_list.append("MXX " + qub + " ANCILLA")
                ret_list.append("MZZ " + qub_control + " ANCILLA")
                ret_list.append("MX ANCILLA")
            elif gate.startswith("qreg"):
                ret_list.append("INIT " + qub)

        return ret_list

    def save_multibody_format(self, op_list):
        with open("multibody.txt", "w") as f:
            for gate in op_list:
                f.write(gate)

    def load_multibody_format(self):
        ret = []
        with open("multibody.txt", "r") as f:
            for line in f:
                ret.append(line)
        return ret
