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

import torch
import torch.nn as nn


class InverseUniformQuantization(nn.Module):
    """See `this page <https://sp-nitech.github.io/sptk/latest/main/dequantize.html>`_
    for details.

    Parameters
    ----------
    abs_max : float > 0
        Absolute maximum value of input.

    n_bit : int >= 1
        Number of quantization bits.

    quantizer : ['mid-rise', 'mid-tread']
        Quantizer.

    """

    def __init__(self, abs_max=1, n_bit=8, quantizer="mid-rise"):
        super(InverseUniformQuantization, self).__init__()

        self.abs_max = abs_max
        self.precomputes = self._precompute(n_bit, quantizer)

        assert 0 < self.abs_max
        assert 1 <= n_bit

    def forward(self, y):
        """Dequantize input.

        Parameters
        ----------
        y : Tensor [shape=(...,)]
            Quantized input.

        Returns
        -------
        Tensor [shape=(...,)]
            Dequantized input.

        Examples
        --------
        >>> x = diffsptk.ramp(-4, 4)
        >>> x
        tensor([-4., -3., -2., -1.,  0.,  1.,  2.,  3.,  4.])
        >>> quantize = diffsptk.UniformQuantization(4, 2)
        >>> dequantize = diffsptk.InverseUniformQuantization(4, 2)
        >>> x2 = dequantize(quantize(x))
        >>> x2
        tensor([-3., -3., -1., -1.,  1.,  1.,  3.,  3.,  3.])

        """
        return self._forward(y, self.abs_max, self.precomputes)

    @staticmethod
    def _forward(y, abs_max, precomputes):
        level, func = precomputes
        y = func(y)
        x = y * (2 * abs_max / level)
        x = torch.clip(x, min=-abs_max, max=abs_max)
        return x

    @staticmethod
    def _func(y, abs_max, n_bit, quantizer):
        precomputes = InverseUniformQuantization._precompute(n_bit, quantizer)
        return InverseUniformQuantization._forward(y, abs_max, precomputes)

    @staticmethod
    def _precompute(n_bit, quantizer):
        if quantizer == 0 or quantizer == "mid-rise":
            level = 1 << n_bit

            def func(y):
                return y - (level // 2 - 0.5)

        elif quantizer == 1 or quantizer == "mid-tread":
            level = (1 << n_bit) - 1

            def func(y):
                return y - (level // 2)

        else:
            raise ValueError(f"quantizer {quantizer} is not supported.")
        return level, func
