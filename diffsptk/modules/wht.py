# ------------------------------------------------------------------------ #
# Copyright 2022 SPTK Working Group                                        #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
# ------------------------------------------------------------------------ #

import numpy as np
import torch
from scipy.linalg import hadamard
from torch import nn

from ..misc.utils import check_size, is_power_of_two, to


class WalshHadamardTransform(nn.Module):
    """Walsh-Hadamard Transform module.

    Parameters
    ----------
    wht_length : int >= 1
        WHT length, :math:`L`, must be a power of 2.

    wht_type : int in [1, 3]
        WHT type. 1: Sequency-ordered, 2: Natural-ordered, 3: Dyadic-ordered.

    """

    def __init__(self, wht_length, wht_type=2):
        super().__init__()

        assert is_power_of_two(wht_length)
        assert 1 <= wht_type <= 3

        self.wht_length = wht_length
        self.register_buffer("W", self._precompute(wht_length, wht_type))

    def forward(self, x):
        """Apply WHT to input.

        Parameters
        ----------
        x : Tensor [shape=(..., L)]
            Input.

        Returns
        -------
        out : Tensor [shape=(..., L)]
            WHT output.

        Examples
        --------
        >>> x = diffsptk.ramp(3)
        >>> wht = diffsptk.WHT(4)
        >>> y = wht(x)
        >>> y
        tensor([ 3., -1., -2.,  0.])
        >>> z = wht(y)
        >>> z
        tensor([0., 1., 2., 3.])

        """
        check_size(x.size(-1), self.wht_length, "dimension of input")
        return self._forward(x, self.W)

    @staticmethod
    def _forward(x, W):
        return torch.matmul(x, W)

    @staticmethod
    def _func(x, wht_type):
        W = WalshHadamardTransform._precompute(
            x.size(-1), wht_type, dtype=x.dtype, device=x.device
        )
        return WalshHadamardTransform._forward(x, W)

    @staticmethod
    def _precompute(length, wht_type, dtype=None, device=None):
        z = 2 ** -(np.log2(length) / 2)
        W = hadamard(length)
        if wht_type == 1:
            sign_changes = np.sum(np.abs(np.diff(W, axis=1)), axis=1)
            W = W[np.argsort(sign_changes)]
        elif wht_type == 2:
            pass
        elif wht_type == 3:
            gray_bits = [
                [int(x) for x in np.binary_repr(i, width=int(np.log2(length)))]
                for i in range(length)
            ]
            binary_bits = np.bitwise_xor.accumulate(gray_bits, axis=1)
            permutation = [int("".join(row), 2) for row in binary_bits.astype(str)]
            sign_changes = np.sum(np.abs(np.diff(W, axis=1)), axis=1)
            W = W[np.argsort(sign_changes)][permutation]
        else:
            raise ValueError
        W = torch.from_numpy(W * z)
        return to(W, dtype=dtype, device=device)
