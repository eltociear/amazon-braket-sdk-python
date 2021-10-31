# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import numpy as np
import pytest
from scipy.linalg import expm

from braket.circuits.gates import X, Y, Z, H, S, T
import braket.circuits.synthesis.one_qubit_decomposition as decomp1q
from braket.circuits.quantum_operator_helpers import eq_up_to_phase
from braket.circuits.synthesis.util import to_su

x = X().to_matrix()
y = Y().to_matrix()
z = Z().to_matrix()
h = H().to_matrix()
s = S().to_matrix()
t = T().to_matrix()


def u(a, b, c):
    return np.array(
        [
            [np.cos(0.5 * a), -np.exp(1j * c) * np.sin(0.5 * a)],
            [np.sin(0.5 * a) * np.exp(1j * b), np.cos(0.5 * a) * np.exp(1j * (b + c))],
        ],
        dtype=np.complex128,
    )


@pytest.mark.parametrize(
    "unitary_test_cases",
    [x, y, z, h, s, t]
    + [
        u(0.12, 0.36, 0.71),
        u(-0.96, 2.74, -4.18),
        u(1.24, 4.12, 2.45),
        u(0.0, 0.1, -0.01),
        u(0.00000001, 0, 0),
    ],
)
def test_one_qubit_decomposition(unitary_test_cases):

    test_decomp = decomp1q.OneQubitDecomposition(unitary_test_cases)

    # Test global phase
    assert np.allclose(test_decomp.phase * to_su(unitary_test_cases), unitary_test_cases)

    # Test zyz decomposition
    circ1 = test_decomp.to_circuit(method="zxz")
    assert eq_up_to_phase(circ1.as_unitary(), unitary_test_cases)

    # Test zxz decomposition
    circ2 = test_decomp.to_circuit(method="zyz")
    assert eq_up_to_phase(circ2.as_unitary(), unitary_test_cases)

    # Test quaternion
    quat = test_decomp.quaternion
    assert np.isclose(np.linalg.norm(quat), 1)

    # Test axis-angle decomposition
    theta = test_decomp.rotation_angle
    vec = test_decomp.canonical_vector

    assert np.allclose(
        test_decomp.phase * expm(-0.5j * theta * (vec[0] * x + vec[1] * y + vec[2] * z)),
        unitary_test_cases,
        atol=1e-6,
        rtol=1e-4,
    )


x_repr = """
OneQubitDecomposition(
  global phase: (6.123233995736766e-17+1j),
  ZYZ decomposition:
    ------Rz--Ry--Rz------
    euler angles: [4.71238898 3.14159265 1.57079633])
  Axis-angle decomposition:
    SU(2) = exp(-0.5j * theta * (xX + yY + zZ))
    canonical vector (x, y, z): [ 1.000000e+00 -6.123234e-17 -0.000000e+00],
    theta: 3.141592653589793,
    quaternion representation: [ 0.000000e+00  1.000000e+00 -6.123234e-17 -0.000000e+00]
)""".strip()


@pytest.mark.parametrize("u, u_repr, u_angle", [(x, x_repr, np.pi)])
def test_one_qubit_decomposition_misc(u, u_repr, u_angle):
    test_decomp = decomp1q.OneQubitDecomposition(u)
    assert test_decomp.__repr__().strip() == u_repr
    assert test_decomp.rotation_angle == u_angle


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("random_test_cases", [np.eye(4)])
def test_one_qubit_decomposition_fail1(random_test_cases):
    decomp1q.OneQubitDecomposition(random_test_cases)


@pytest.mark.xfail(raises=NotImplementedError)
@pytest.mark.parametrize(
    "unitary_test_cases",
    [x, y, z, h, s, t]
    + [
        u(0.12, 0.36, 0.71),
        u(-0.96, 2.74, -4.18),
        u(1.24, 4.12, 2.45),
        u(0.0, 0.1, -0.01),
    ],
)
def test_one_qubit_decomposition_fail2(unitary_test_cases):
    test_decomp = decomp1q.OneQubitDecomposition(unitary_test_cases)
    test_decomp.euler_angles("zzz")
