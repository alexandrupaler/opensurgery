'''
Decompose a list of strings into another list of strings.
This is very similar to how SurfBraid http://alexandrupaler.github.io/quantjs works

For a first round of resource estimations from Cirq, the Clifford + T gates are
decomposed in replace_gates_with_multibody
'''

from skc.operator import *
from skc.dawson.factor import *
from skc.dawson import *
from skc.compose import *
from skc.basis import *

import math

class PrepareCircuit:
    def __init__(self):
        self.H2 = None
        print("Prepare Circuit")

    def initialise_skc(self):
        '''
        Configure the SK compiler
        :return: nothing
        '''
        if self.H2 is None:
            self.H2 = get_hermitian_basis(d=2)
            # Prepare the compiler
            sk_set_factor_method(dawson_group_factor)
            sk_set_basis(self.H2)
            # TODO: Paler - what is this for?
            sk_set_axis(X_AXIS)
            sk_build_tree("su2", 15)

        return

    def decompose_SK_on_gate(self, pi_fraction, which_axis=(0, 0, 1)):
        '''
        Assume Z rotation always, and decompose the rotations accordingly?
        :param pi_fraction:
        :param which_axis: Tuple indicating with bits which axis the rotation is around
        :return:
        '''

        self.initialise_skc()

        axis = cart3d_to_h2(
            x = which_axis[0],
            y = which_axis[1],
            z = which_axis[2]
        )

        # the rotation angle
        theta = math.pi * pi_fraction

        # Compose a unitary to compile
        matrix_U = axis_to_unitary(axis, theta, self.H2)
        op_U = Operator(name="U", matrix=matrix_U)

        n = 4
        # print("U= " + str(matrix_U))
        # print("n= " + str(n))

        Un = solovay_kitaev(op_U, n)

        # print("Approximated U: " + str(Un))
        # print("Un= " + str(Un.matrix))

        # print("trace_dist(U,Un)= " + str(trace_distance(Un.matrix, op_U.matrix)))
        # print("fowler_dist(U,Un)= " + str(fowler_distance(Un.matrix, op_U.matrix)))

        # see skc/operator.py for the ancestors member
        return self.parse_skc_compiler_ancestors(Un.ancestors)

    def parse_skc_compiler_ancestors(self, ancestors):
        ret_list = []
        for a in ancestors:
            gate = str(a).replace("d", "")
            ret_list.append(gate)

        # print("ancestors" + str(ret_list))
        return ret_list


    def parse_to_my_string_format(self, cirq_circuit):
        # the first 5 lines are header
        str_s = [s for s in cirq_circuit.split("\n") if s.strip() != ''][4:]

        # replace rx with rz
        # replace ry with rz
        tmp_str_s = []
        for gate in str_s:
            qubs = gate.split(" ")[1]
            if gate.startswith("rx"):
                tmp_str_s.append("h " + qubs)
                tmp_str_s.append(gate.replace("rx", "rz"))
                tmp_str_s.append("h " + qubs)
            elif gate.startswith("ry"):
                tmp_str_s.append("rz(pi*0.5) " + qubs)
                tmp_str_s.append(gate.replace("ry", "rz"))
                tmp_str_s.append("rz(pi*0.5) " + qubs)
            else:
                tmp_str_s.append(gate)

        # overwrite str_s
        str_s = tmp_str_s

        # other replacements
        # some minus angles are just like the normal rotation, because I do care about resource estimation
        # and not computational correctness
        str_s = [s.replace("h", "H") for s in str_s]

        # half pi rotations
        str_s = [s.replace("rz(pi*0.5)", "S") for s in str_s]
        str_s = [s.replace("rz(pi*-0.5)", "S") for s in str_s]
        str_s = [s.replace("rx(pi*0.5)", "V") for s in str_s]
        str_s = [s.replace("rx(pi*-0.5)", "V") for s in str_s]

        # quarter pi rotations
        str_s = [s.replace("rz(pi*0.25)", "T") for s in str_s]
        str_s = [s.replace("rz(pi*-0.25)", "T") for s in str_s]

        # pi + fraction angles - works only for the RZ
        str_s = [s.replace("rz(pi*1.5)", "T") for s in str_s]
        str_s = [s.replace("rz(pi*-1.5)", "T") for s in str_s]

        # pi angles are the pauli gates?
        str_s = [s.replace("rx(pi*1.0)", "x") for s in str_s]
        str_s = [s.replace("rx(pi*-1.0)", "x") for s in str_s]
        str_s = [s.replace("ry(pi*1.0)", "y") for s in str_s]
        str_s = [s.replace("ry(pi*-1.0)", "y") for s in str_s]
        str_s = [s.replace("rz(pi*1.0)", "z") for s in str_s]
        str_s = [s.replace("rz(pi*-1.0)", "z") for s in str_s]

        str_s = [s.replace("cx", "CNOT") for s in str_s]

        str_s = [s.replace("q[", "")
                     .replace("]", "")
                     .replace(",", " ")
                     .replace(";", "")
                     .strip() for s in str_s]

        str_s = [s.replace("cz", "CPHASE") for s in str_s]

        return str_s

    def decompose_arbitrary_rotations(self, gate_list):
        ret_list = []

        dictionary_decomposed_rotations = {}

        for gate in gate_list:
            if gate[0] == "r":
                which_axis = (0, 0, 0)
                if gate[1] == "x":
                    which_axis = (1, 0, 0)
                elif gate[1] == "y":
                    which_axis = (0, 1, 0)
                elif gate[1] == "z":
                    which_axis = (0, 0, 1)

                # split at "pi"
                half_part = (gate.split("pi"))[1].replace("*", "").replace(")", "")
                # take the angle and not the qubits the gate is applied to
                angle_part_string = half_part.split(" ")[0]
                angle_float = math.fabs(float(angle_part_string))

                qubit_id = half_part.split(" ")[1]

                # remove 2pi factors
                while angle_float > 2:
                    angle_float -= 2

                if angle_float == 0.5:
                    ret_list.append("S " + qubit_id)
                    continue

                if angle_float not in dictionary_decomposed_rotations:
                    print(gate, "decompose")
                    # decomposition
                    decompo = self.decompose_SK_on_gate(angle_float, which_axis)
                    # store the decomposition
                    dictionary_decomposed_rotations[angle_float] = decompo
                    # into the returned list

                for dec in dictionary_decomposed_rotations[angle_float]:
                    ret_list.append(dec + " " + qubit_id)

            else:
                ret_list.append(gate)

        return ret_list


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
            elif gate.startswith("V"):
                ret_list.append(gate)
            elif gate.startswith("CPHASE"):
                qub_control = gate.split(" ")[-2]
                ret_list.append("H " + qub)

                cnot_gate = "CNOT " + qub_control + " " + qub
                the_cnot_list = self.replace_gates_with_multibody([cnot_gate])
                ret_list.extend(the_cnot_list)

                ret_list.append("H " + qub)
            elif gate.startswith("CNOT"):
                qub_control = gate.split(" ")[-2]
                ret_list.append("ANCILLA 0")
                ret_list.append("MXX " + qub + " ANCILLA")
                ret_list.append("MZZ " + qub_control + " ANCILLA")
                ret_list.append("MX ANCILLA")
            elif gate.startswith("qreg"):
                ret_list.append("INIT " + qub)
            elif gate.startswith(("x", "y", "z")):
                # do nothing, skip
                # skip Pauli gates? - yes because in MXX/MZZ format these can be tracked, because the M?? are CNOTs in fact
                continue
            else:
                # add the gate to the list -- we do not know what it is, or if it will be decomposed later
                ret_list.append(gate)

        return ret_list

    def save_multibody_format(self, op_list):
        with open("multibody.txt", "w") as f:
            for gate in op_list:
                f.write(gate)

    def load_multibody_format(self):
        ret = []
        with open("output_instructions.txt", "r") as f:
            for line in f:
                ret.append(line.strip())
        return ret
