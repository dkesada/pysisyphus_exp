import itertools as it

import numpy as np

from pysisyphus.Geometry import Geometry
from pysisyphus.intcoords.derivatives import d2q_b, d2q_a, d2q_d
from pysisyphus.intcoords import Stretch, Bend, Torsion


def fin_diff_B(primitive, coords3d, delta=1e-6):
    """Derivatives of a primitive internal gradient wrt its defining
    cartesian coordinates."""
    displacement_inds = [(i, j) for i, j in it.product(primitive.indices, (0, 1, 2))]

    B_grads = list()
    for grad_atom_ind, grad_ax_ind in displacement_inds:
        # Calculate the derivative of an entry of the Wilson B-matrix.
        for atom_ind, ax_ind in displacement_inds:
            plus = coords3d.copy()
            plus[atom_ind, ax_ind] += delta
            _, plus_val = primitive.calculate(plus, gradient=True)
            plus_val = plus_val.reshape(-1, 3)
            minus = coords3d.copy()
            minus[atom_ind, ax_ind] -= delta
            _, minus_val = primitive.calculate(minus, gradient=True)
            minus_val = minus_val.reshape(-1, 3)
            # Select the appropriate item of the primitive internal gradient
            B_grad = (plus_val[grad_atom_ind, grad_ax_ind]
                      - minus_val[grad_atom_ind, grad_ax_ind]) / (2 * delta)
            B_grads.append(B_grad)
    B_grads = np.array(B_grads)
    return B_grads
