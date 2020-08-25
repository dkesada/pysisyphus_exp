import numpy as np

# from pysisyphus.helpers import fit_rigid
from pysisyphus.optimizers.Optimizer import Optimizer
from pysisyphus.optimizers.hessian_updates import double_damp
from pysisyphus.optimizers.restrict_step import scale_by_max_step

# [1] Nocedal, Wright - Numerical Optimization, 2006
# [2] http://dx.doi.org/10.1016/j.jcp.2013.08.044
#     Badreddine, 2013
# [3] https://arxiv.org/abs/2006.08877
#     Goldfarb, 2020

class BFGS(Optimizer):

    def __init__(self, geometry, *args, update="bfgs", **kwargs):
        super().__init__(geometry, *args, **kwargs)

        self.update = update

        update_funcs = {
            "bfgs": self.bfgs_update,
            "damped": self.damped_bfgs_update,
            "double": self.double_damped_bfgs_update,
        }
        self.update_func = update_funcs[self.update]

    def prepare_opt(self):
        # Inverse Hessian
        self.H = self.eye

    @property
    def eye(self):
        size = self.geometry.coords.size
        return np.eye(size)

    def bfgs_update(self, s, y):
        rho = 1 / s.dot(y)
        V = self.eye - rho*np.outer(s, y)
        self.H = V.dot(self.H).dot(V.T) + rho*np.outer(s, s)

    def double_damped_bfgs_update(self, s, y, mu_1=0.2, mu_2=0.2):
        """Double damped BFGS update of inverse Hessian.

        See [3]. Potentially updates s and y."""

        s, y = double_damp(self.H, s, y, mu_1, mu_2, self.logger)
        self.bfgs_update(s, y)

    def damped_bfgs_update(self, s, y, mu_1=0.2):
        """Damped BFGS update of inverse Hessian.

        Potentially updates s.
        See Section 3.2 of [2], Eq. (30) - (33). There is a typo ;)
        It should be
            H_{k+1} = V_k H_k V_k^T + ...
        instead of
            H_{k+1} = V_k^T H_k V_k + ...
        """
        self.double_damped_bfgs_update(s, y, mu_2=None)

    def optimize(self):
        # if self.is_cos and self.align and self.cur_cycle > 0:
           # rotated = fit_rigid(
                        # self.geometry,
                        # (self.forces[-1], self.steps[-1]),
                        # hessian=self.H
           # )
           # (prev_step, prev_forces), _, self.H = rotated
        # elif self.cur_cycle > 0:
           # prev_forces = self.forces[-1]
           # prev_step = self.steps[-1]

        forces = self.geometry.forces
        energy = self.geometry.energy
        self.forces.append(forces)
        self.energies.append(energy)

        if self.cur_cycle > 0:
            # Gradient difference
            y = self.forces[-2] - forces
            # y = prev_forces - forces
            # Coordinate difference / step
            s = self.steps[-1]
            # s = prev_step
            # Curvature condition
            sy = s.dot(y)
            self.log(f"s·y={sy:.6f}")
            self.update_func(s, y)
            step_type = "BFGS"
            step = self.H.dot(forces)
        else:
            step = forces
            step_type = "Steepest Descent"
        self.log(f"Calcualted {step_type} step")
        unscaled_norm = np.linalg.norm(step)
        step = scale_by_max_step(step, self.max_step)
        scaled_norm = np.linalg.norm(step)
        self.log(f"Unscaled norm(step)={unscaled_norm:.4f}")
        self.log(f"  Scaled norm(step)={scaled_norm:.4f}")

        return step
