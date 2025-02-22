from __future__ import annotations

from collections import Counter
from functools import singledispatch
from typing import Any, Union

from torch import Tensor, no_grad

from qadence import backend_factory
from qadence.backend import BackendConfiguration, BackendName
from qadence.blocks import AbstractBlock
from qadence.circuit import QuantumCircuit
from qadence.register import Register
from qadence.types import DiffMode
from qadence.utils import Endianness

# Modules to be automatically added to the qadence namespace
__all__ = ["run", "sample", "expectation"]


@singledispatch
def run(
    x: Union[QuantumCircuit, AbstractBlock, Register, int],
    *args: Any,
    values: dict = {},
    state: Tensor = None,
    backend: BackendName = BackendName.PYQTORCH,
    endianness: Endianness = Endianness.BIG,
    configuration: Union[BackendConfiguration, dict, None] = None,
) -> Tensor:
    """Convenience wrapper for the `QuantumModel.run` method.  This is a
    `functools.singledispatch`ed function so it can be called with a number of different arguments.
    See the examples of the [`expectation`][qadence.execution.expectation] function. This function
    works exactly the same.

    Arguments:
        x: Circuit, block, or (register+block) to run.
        values: User-facing parameter dict.
        state: Initial state.
        backend: Name of the backend to run on.
        endianness: The target device endianness.
        configuration: The backend configuration.

    Returns:
        A wavefunction
    """
    raise ValueError(f"Cannot run {type(x)}")


@run.register
def _(
    circuit: QuantumCircuit,
    values: dict = {},
    state: Tensor = None,
    backend: BackendName = BackendName.PYQTORCH,
    endianness: Endianness = Endianness.BIG,
    configuration: Union[BackendConfiguration, dict, None] = None,
) -> Tensor:
    bknd = backend_factory(backend, configuration=configuration)
    conv = bknd.convert(circuit)
    with no_grad():
        return bknd.run(
            circuit=conv.circuit,
            param_values=conv.embedding_fn(conv.params, values),
            state=state,
            endianness=endianness,
        )


@run.register
def _(register: Register, block: AbstractBlock, **kwargs: Any) -> Tensor:
    return run(QuantumCircuit(register, block), **kwargs)


@run.register
def _(n_qubits: int, block: AbstractBlock, **kwargs: Any) -> Tensor:
    return run(Register(n_qubits), block, **kwargs)


@run.register
def _(block: AbstractBlock, **kwargs: Any) -> Tensor:
    return run(Register(block.n_qubits), block, **kwargs)


@singledispatch
def sample(
    x: Union[QuantumCircuit, AbstractBlock, Register, int],
    *args: Any,
    values: dict = {},
    state: Union[Tensor, None] = None,
    n_shots: int = 100,
    backend: BackendName = BackendName.PYQTORCH,
    endianness: Endianness = Endianness.BIG,
    configuration: Union[BackendConfiguration, dict, None] = None,
) -> list[Counter]:
    """Convenience wrapper for the `QuantumModel.sample` method.  This is a
    `functools.singledispatch`ed function so it can be called with a number of different arguments.
    See the examples of the [`expectation`][qadence.execution.expectation] function. This function
    works exactly the same.

    Arguments:
        x: Circuit, block, or (register+block) to run.
        values: User-facing parameter dict.
        state: Initial state.
        n_shots: Number of shots per element in the batch.
        backend: Name of the backend to run on.
        endianness: The target device endianness.
        configuration: The backend configuration.

    Returns:
        A list of Counter instances with the sample results
    """
    raise ValueError(f"Cannot sample from {type(x)}")


@sample.register
def _(
    circuit: QuantumCircuit,
    values: dict = {},
    state: Union[Tensor, None] = None,
    n_shots: int = 100,
    backend: BackendName = BackendName.PYQTORCH,
    endianness: Endianness = Endianness.BIG,
    configuration: Union[BackendConfiguration, dict, None] = None,
) -> list[Counter]:
    bknd = backend_factory(backend, configuration=configuration)
    conv = bknd.convert(circuit)
    return bknd.sample(
        circuit=conv.circuit,
        param_values=conv.embedding_fn(conv.params, values),
        n_shots=n_shots,
        state=state,
        endianness=endianness,
    )


@sample.register
def _(register: Register, block: AbstractBlock, **kwargs: Any) -> Tensor:
    return sample(QuantumCircuit(register, block), **kwargs)


@sample.register
def _(n_qubits: int, block: AbstractBlock, **kwargs: Any) -> Tensor:
    return sample(Register(n_qubits), block, **kwargs)


@sample.register
def _(block: AbstractBlock, **kwargs: Any) -> Tensor:
    reg = Register(block.n_qubits)
    return sample(reg, block, **kwargs)


@singledispatch
def expectation(
    x: Union[QuantumCircuit, AbstractBlock, Register, int],
    observable: Union[list[AbstractBlock], AbstractBlock],
    values: dict = {},
    state: Tensor = None,
    backend: BackendName = BackendName.PYQTORCH,
    diff_mode: Union[DiffMode, str, None] = None,
    endianness: Endianness = Endianness.BIG,
    configuration: Union[BackendConfiguration, dict, None] = None,
) -> Tensor:
    """Convenience wrapper for the `QuantumModel.expectation` method.  This is a
    `functools.singledispatch`ed function so it can be called with a number of different arguments
    (see in the examples).

    Arguments:
        x: Circuit, block, or (register+block) to run.
        observable: Observable(s) w.r.t. which the expectation is computed.
        values: User-facing parameter dict.
        state: Initial state.
        backend: Name of the backend to run on.
        diff_mode: Which differentiation mode to use.
        endianness: The target device endianness.
        configuration: The backend configuration.

    Returns:
        A wavefunction


    ```python exec="on" source="material-block"
    from qadence import RX, Z, Register, QuantumCircuit, expectation

    reg = Register(1)
    block = RX(0, 0.5)
    observable = Z(0)
    circ = QuantumCircuit(reg, block)

    # You can compute the expectation for a
    # QuantumCircuit with a given observable.
    expectation(circ, observable)

    # You can also use only a block.
    # In this case the register is constructed automatically to
    # Register.line(block.n_qubits)
    expectation(block, observable)

    # Or a register and block
    expectation(reg, block, observable)
    ```"""

    raise ValueError(f"Cannot execute {type(x)}")


@expectation.register
def _(
    circuit: QuantumCircuit,
    observable: Union[list[AbstractBlock], AbstractBlock],
    values: dict = {},
    state: Tensor = None,
    backend: BackendName = BackendName.PYQTORCH,
    diff_mode: Union[DiffMode, str, None] = None,
    endianness: Endianness = Endianness.BIG,
    configuration: Union[BackendConfiguration, dict, None] = None,
) -> Tensor:
    observable = observable if isinstance(observable, list) else [observable]
    bknd = backend_factory(backend, configuration=configuration)
    conv = bknd.convert(circuit, observable)

    def _expectation() -> Tensor:
        return bknd.expectation(
            circuit=conv.circuit,
            observable=conv.observable,  # type: ignore[arg-type]
            param_values=conv.embedding_fn(conv.params, values),
            state=state,
            endianness=endianness,
        )

    # Do not compute gradients if no diff_mode is provided.
    if diff_mode is None:
        with no_grad():
            return _expectation()
    else:
        return _expectation()


@expectation.register
def _(
    register: Register,
    block: AbstractBlock,
    observable: Union[list[AbstractBlock], AbstractBlock],
    **kwargs: Any,
) -> Tensor:
    return expectation(QuantumCircuit(register, block), observable, **kwargs)


@expectation.register
def _(
    n_qubits: int,
    block: AbstractBlock,
    observable: Union[list[AbstractBlock], AbstractBlock],
    **kwargs: Any,
) -> Tensor:
    reg = Register(n_qubits)
    return expectation(QuantumCircuit(reg, block), observable, **kwargs)


@expectation.register
def _(
    block: AbstractBlock, observable: Union[list[AbstractBlock], AbstractBlock], **kwargs: Any
) -> Tensor:
    reg = Register(block.n_qubits)
    return expectation(QuantumCircuit(reg, block), observable, **kwargs)
