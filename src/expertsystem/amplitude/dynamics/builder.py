"""Build :mod:`.lineshape` with correct variable names and values."""

import inspect
from collections import OrderedDict
from typing import Callable, Dict, Optional, Tuple

import attr
import sympy as sy

from expertsystem.particle import Particle

from .lineshape import (
    relativistic_breit_wigner,
    relativistic_breit_wigner_with_ff,
)

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore


@attr.s(frozen=True)
class TwoBodyKinematicVariableSet:
    in_edge_inv_mass: sy.Symbol = attr.ib()
    out_edge_inv_mass1: sy.Symbol = attr.ib()
    out_edge_inv_mass2: sy.Symbol = attr.ib()
    helicity_theta: sy.Symbol = attr.ib()
    helicity_phi: sy.Symbol = attr.ib()
    angular_momentum: Optional[int] = attr.ib(default=None)


def create_non_dynamic(
    particle: Particle, variable_pool: TwoBodyKinematicVariableSet
) -> Tuple[sy.Expr, Dict[sy.Symbol, float]]:
    # pylint: disable=unused-argument
    return (1, {})


def create_relativistic_breit_wigner(
    particle: Particle, variable_pool: TwoBodyKinematicVariableSet
) -> Tuple[sy.Expr, Dict[sy.Symbol, float]]:
    inv_mass = variable_pool.in_edge_inv_mass
    res_mass = sy.Symbol(f"m_{particle.name}")
    res_width = sy.Symbol(f"Gamma_{particle.name}")

    return (
        relativistic_breit_wigner(
            inv_mass,
            res_mass,
            res_width,
        ),
        {res_mass: particle.mass, res_width: particle.width},
    )


def create_relativistic_breit_wigner_with_ff(
    particle: Particle, variable_pool: TwoBodyKinematicVariableSet
) -> Tuple[sy.Expr, Dict[sy.Symbol, float]]:
    if variable_pool.angular_momentum is None:
        raise ValueError(
            "Angular momentum is not defined but is required in the form factor!"
        )

    inv_mass = variable_pool.in_edge_inv_mass
    res_mass = sy.Symbol(f"m_{particle.name}")
    res_width = sy.Symbol(f"Gamma_{particle.name}")
    product1_inv_mass = variable_pool.out_edge_inv_mass1
    product2_inv_mass = variable_pool.out_edge_inv_mass2
    angular_momentum = variable_pool.angular_momentum
    meson_radius = sy.Symbol(f"d_{particle.name}")

    return (
        relativistic_breit_wigner_with_ff(
            inv_mass,
            res_mass,
            res_width,
            product1_inv_mass,
            product2_inv_mass,
            angular_momentum,
            meson_radius,
        ),
        {res_mass: particle.mass, res_width: particle.width, meson_radius: 1},
    )


class ResonanceDynamicsBuilder(Protocol):
    """Protocol that is used by `.set_resonance_dynamics`.

    Follow this `~typing.Protocol` when defining a builder that is to be used
    by `.set_resonance_dynamics`. For an example, see
    `.create_relativistic_breit_wigner`, which creates a
    `.relativistic_breit_wigner`.
    """

    def __call__(
        self, particle: Particle, variable_pool: TwoBodyKinematicVariableSet
    ) -> Tuple[sy.Expr, Dict[sy.Symbol, float]]:
        ...


def verify_signature(builder: Callable) -> None:
    """Check signature of a builder function dynamically.

    Dynamically check whether a builder has the same signature as
    `.ResonanceDynamicsBuilder`. This function is needed because
    `typing.runtime_checkable` does only checks members and methods, not the
    signature of those methods.
    """
    signature = inspect.signature(builder)
    if signature.return_annotation != __EXPECTED.return_annotation:
        raise ValueError(
            f'Builder "{builder.__name__}" has return type {__EXPECTED.return_annotation};'
            f" expected {signature.return_annotation}"
        )
    expected_parameters = OrderedDict(__EXPECTED.parameters.items())
    del expected_parameters["self"]
    assert signature.return_annotation == __EXPECTED.return_annotation
    if signature.parameters != expected_parameters:
        raise ValueError(
            f'Builder "{builder.__name__}" has parameters\n'
            f"  {list(signature.parameters.values())}\n"
            "This should be\n"
            f"  {list(expected_parameters.values())}"
        )


__EXPECTED = inspect.signature(ResonanceDynamicsBuilder.__call__)