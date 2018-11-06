'''
works only with latest github versions of openfermion, cirq and openfermioncirq
'''

import time
import cirq
import openfermion as of
import openfermioncirq as ofc

from skc.operator import *
from skc.dawson.factor import *
from skc.dawson import *
from skc.compose import *
from skc.basis import *

import math

import random


class CirqInterface:
    def __init__(self):
        # circuits_1 = self.kevin_hubbard_cirq()
        # circuits_2 = self.kevin_lih_cirq()
        # print(circuits_1[0].to_qasm())

        # self.run_SK_on_gate()
        return

    def random_circuit(self, nr_qubits, nr_gates):
        c = cirq.Circuit()

        qubits = []
        for i in range(nr_qubits):
            qubits.append(cirq.NamedQubit("q" + str(i)))

        # S 0, T 1, H 2, CNOT 3
        for i in range(nr_gates):
            r_gate_type = random.randint(0, 3)
            r_qub = random.randint(0, len(qubits) - 1)

            if r_gate_type == 0:
                c.append(cirq.S(qubits[r_qub]))
            elif r_gate_type == 1:
                c.append(cirq.T(qubits[r_qub]))
            elif r_gate_type == 2:
                c.append(cirq.H(qubits[r_qub]))
            elif r_gate_type == 3:
                r_qub2 = random.randint(0, len(qubits) - 1)
                while r_qub2 == r_qub:
                    r_qub2 = random.randint(0, len(qubits) - 1)
                c.append(cirq.CNOT(control=qubits[r_qub], target=qubits[r_qub2]))

        # print(c.to_qasm())

        return c

    def run_SK_on_gate(self):
        H2 = get_hermitian_basis(d=2)
        axis = cart3d_to_h2(x=0, y=0, z=1)
        theta = math.pi / 16  # 45 degrees

        # Compose a unitary to compile
        matrix_U = axis_to_unitary(axis, theta, H2)
        op_U = Operator(name="U", matrix=matrix_U)

        n = 4
        print("U= " + str(matrix_U))
        print("n= " + str(n))

        # Prepare the compiler
        sk_set_factor_method(dawson_group_factor)
        sk_set_basis(H2)
        sk_set_axis(X_AXIS)
        sk_build_tree("su2", 15)

        Un = solovay_kitaev(op_U, n)
        print("Approximated U: " + str(Un))

        print("Un= " + str(Un.matrix))

        # print("trace_dist(U,Un)= " + str(trace_distance(Un.matrix, op_U.matrix)))
        # print("fowler_dist(U,Un)= " + str(fowler_distance(Un.matrix, op_U.matrix)))

    # Convert circuits to CZ and single-qubit gates
    # ---------------------------------------------
    def kevin_optimize_circuit(self, circuit):
        cirq.DropNegligible().optimize_circuit(circuit)
        cirq.ConvertToCzAndSingleGates().optimize_circuit(circuit)

    def kevin_hubbard_cirq(self):
        # Create Hubbard model Hamiltonian
        # --------------------------------
        x_dim = 3
        y_dim = 2
        n_sites = x_dim * y_dim
        n_modes = 2 * n_sites

        tunneling = 1.0
        coulomb = 4.0

        hubbard_model = of.fermi_hubbard(x_dim, y_dim, tunneling, coulomb)

        # Reorder indices
        hubbard_model = of.reorder(hubbard_model, of.up_then_down)

        # Convert to DiagonalCoulombHamiltonian
        hubbard_hamiltonian = of.get_diagonal_coulomb_hamiltonian(hubbard_model)

        # Create qubits
        qubits = cirq.LineQubit.range(n_modes)

        # State preparation circuit for eigenstate of one-body term
        # ---------------------------------------------------------
        # Set the pseudo-particle orbitals to fill
        up_orbitals = range(n_sites // 2)
        down_orbitals = range(n_sites // 2)

        # Create the circuit
        hubbard_state_preparation_circuit = cirq.Circuit.from_ops(
            ofc.prepare_gaussian_state(
                qubits,
                of.QuadraticHamiltonian(hubbard_hamiltonian.one_body),
                occupied_orbitals=(up_orbitals, down_orbitals)
            ),
            strategy=cirq.InsertStrategy.EARLIEST
        )

        # Trotter simulation circuit
        # --------------------------
        n_steps = 10
        order = 0

        hubbard_simulation_circuit = cirq.Circuit.from_ops(
            ofc.simulate_trotter(
                qubits,
                hubbard_hamiltonian,
                time=1.0,
                n_steps=n_steps,
                order=order,
                algorithm=ofc.trotter.LINEAR_SWAP_NETWORK
            ),
            strategy=cirq.InsertStrategy.EARLIEST
        )

        t0 = time.time()
        self.kevin_optimize_circuit(hubbard_state_preparation_circuit)
        self.kevin_optimize_circuit(hubbard_simulation_circuit)
        t1 = time.time()

        print('Optimizing circuits took {} seconds'.format(t1 - t0))
        # print(hubbard_state_preparation_circuit.to_text_diagram(transpose=True))

        return hubbard_state_preparation_circuit, hubbard_simulation_circuit

    def kevin_lih_cirq(self):
        x_dim = 3
        y_dim = 2
        n_sites = x_dim * y_dim
        n_modes = 2 * n_sites

        # Create LiH Hamiltonian
        # ----------------------
        bond_length = 1.45
        geometry = [('Li', (0., 0., 0.)), ('H', (0., 0., bond_length))]
        n_active_electrons = 4
        n_active_orbitals = 4
        lih_hamiltonian = of.load_molecular_hamiltonian(
            geometry, 'sto-3g', 1, format(bond_length), n_active_electrons, n_active_orbitals)

        # Generate qubits
        n_qubits = of.count_qubits(lih_hamiltonian)
        qubits = cirq.LineQubit.range(n_qubits)

        # State preparation circuit for eigenstate of one-body term
        # ---------------------------------------------------------
        # Set the pseudo-particle orbitals to fill
        occupied_orbitals = range(n_qubits // 2)

        # State preparation circuit for eigenstate of one-body term
        # ---------------------------------------------------------
        # Set the pseudo-particle orbitals to fill
        up_orbitals = range(n_sites // 2)
        down_orbitals = range(n_sites // 2)

        # Create the circuit
        lih_state_preparation_circuit = cirq.Circuit.from_ops(
            ofc.prepare_gaussian_state(
                qubits,
                of.QuadraticHamiltonian(lih_hamiltonian.one_body_tensor),
                occupied_orbitals=(up_orbitals, down_orbitals)
            ),
            strategy=cirq.InsertStrategy.EARLIEST
        )

        # Trotter simulation circuit
        # --------------------------
        n_steps = 10
        order = 0

        lih_simulation_circuit = cirq.Circuit.from_ops(
            ofc.simulate_trotter(
                qubits,
                lih_hamiltonian,
                time=1.0,
                n_steps=n_steps,
                order=order,
                algorithm=ofc.trotter.LOW_RANK
            ),
            strategy=cirq.InsertStrategy.EARLIEST
        )

        t0 = time.time()
        self.kevin_optimize_circuit(lih_state_preparation_circuit)
        self.kevin_optimize_circuit(lih_simulation_circuit)
        t1 = time.time()

        print('Optimizing circuits took {} seconds'.format(t1 - t0))
        # print(lih_state_preparation_circuit.to_text_diagram(transpose=True))

        return lih_state_preparation_circuit, lih_simulation_circuit
