from __future__ import annotations

import numpy as np
import sympy
import torch

from qadence import CNOT, RX, RZ, Parameter, QuantumCircuit, chain, total_magnetization
from qadence.backends.pyqtorch.backend import Backend as PyQTorchBackend

torch.manual_seed(42)


def circuit(n_qubits):
    """Helper function to make an example circuit"""

    x = Parameter("x", trainable=False)
    y = Parameter("y", trainable=False)
    theta = Parameter("theta")

    fm = chain(RX(0, 3 * x), RX(1, sympy.exp(y)), RX(0, theta), RZ(1, np.pi / 2))
    ansatz = CNOT(0, 1)
    block = chain(fm, ansatz)

    circ = QuantumCircuit(n_qubits, block)

    return circ


if __name__ == "__main__":
    torch.manual_seed(42)
    n_qubits = 2
    batch_size = 5

    # Making circuit with AD
    circ = circuit(n_qubits)
    observable = total_magnetization(n_qubits=n_qubits)
    backend = PyQTorchBackend()
    pyq_circ, pyq_obs, embed, params = backend.convert(circ, observable)

    batch_size = 5
    values = {
        "x": torch.rand(batch_size, requires_grad=True),
        "y": torch.rand(batch_size, requires_grad=True),
    }

    wf = backend.run(pyq_circ, embed(params, values))
    samples = backend.sample(pyq_circ, embed(params, values))
    expval = backend.expectation(pyq_circ, pyq_obs, embed(params, values))
    dexpval_x = torch.autograd.grad(
        expval, values["x"], torch.ones_like(expval), retain_graph=True
    )[0]
    dexpval_y = torch.autograd.grad(
        expval, values["y"], torch.ones_like(expval), retain_graph=True
    )[0]

    print(f"Statevector: {wf}")
    print(f"Samples: {samples}")
    print(f"Gradient w.r.t. 'x': {dexpval_x}")
    print(f"Gradient w.r.t. 'y': {dexpval_y}")
