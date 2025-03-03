from __future__ import annotations

import numpy as np
import pytest
import torch
from metrics import PULSER_GPSR_ACCEPTANCE

from qadence import DifferentiableBackend, DiffMode, Parameter, QuantumCircuit, add_interaction
from qadence.backends.pulser import Backend as PulserBackend
from qadence.backends.pyqtorch import Backend as PyQBackend
from qadence.blocks import chain
from qadence.constructors import total_magnetization
from qadence.operations import RX, RY, AnalogRot, AnalogRX, wait


def circuit(circ_id: int) -> QuantumCircuit:
    """Helper function to make an example circuit"""

    x = Parameter("x", trainable=False)

    if circ_id == 1:
        block = chain(RX(0, x), RY(1, x))
    elif circ_id == 2:
        block = chain(AnalogRot(duration=1000 * x / 3.0, omega=3.0))
    if circ_id == 3:
        block = chain(AnalogRX(x))
    elif circ_id == 4:
        block = chain(
            AnalogRX(np.pi / 2),
            AnalogRot(duration=1000 * x / 3.0, omega=4.0, delta=3.0),
            wait(500),
            AnalogRX(np.pi / 2),
        )

    circ = QuantumCircuit(2, block)

    return circ


@pytest.mark.slow
@pytest.mark.parametrize(
    "circ_id",
    [1, 2, 3, 4],
)
def test_pulser_gpsr(circ_id: int) -> None:
    torch.manual_seed(42)
    np.random.seed(42)

    if circ_id == 1:
        spacing = 30.0
    else:
        spacing = 8.0

    # define circuits
    circ = circuit(circ_id)
    circ_pyq = add_interaction(circ, spacing=spacing)

    # create input values
    xs = torch.linspace(1, 2 * np.pi, 30, requires_grad=True)
    values = {"x": xs}

    obs = total_magnetization(2)

    # run with pyq backend
    pyq_backend = PyQBackend()
    conv = pyq_backend.convert(circ_pyq, obs)
    pyq_circ, pyq_obs, embedding_fn, params = conv
    diff_backend = DifferentiableBackend(pyq_backend, diff_mode=DiffMode.AD)
    expval_pyq = diff_backend.expectation(pyq_circ, pyq_obs, embedding_fn(params, values))
    dexpval_x_pyq = torch.autograd.grad(
        expval_pyq, values["x"], torch.ones_like(expval_pyq), create_graph=True
    )[0]

    # run with pulser backend
    pulser_backend = PulserBackend(config={"spacing": spacing})  # type: ignore[arg-type]
    conv = pulser_backend.convert(circ, obs)
    pulser_circ, pulser_obs, embedding_fn, params = conv
    diff_backend = DifferentiableBackend(pulser_backend, diff_mode=DiffMode.GPSR, shift_prefac=0.2)
    expval_pulser = diff_backend.expectation(pulser_circ, pulser_obs, embedding_fn(params, values))
    dexpval_x_pulser = torch.autograd.grad(
        expval_pulser, values["x"], torch.ones_like(expval_pulser), create_graph=True
    )[0]

    # acceptance is checked by calculating mean absolute deviation between every derivative value
    # obtained with pyq and pulser backends
    assert (
        torch.mean(torch.abs(dexpval_x_pyq - dexpval_x_pulser)).item() < PULSER_GPSR_ACCEPTANCE
    ), "df/dx not equal."
