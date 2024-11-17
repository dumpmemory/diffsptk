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

import pytest
import torch

import diffsptk


@pytest.mark.parametrize("device", ["cpu", "cuda"])
@pytest.mark.parametrize("exact", [False, True])
def test_analysis_synthesis(device, exact, verbose=False):
    if device == "cuda" and not torch.cuda.is_available():
        return

    x, sr = diffsptk.read(
        "assets/data.wav",
        double=torch.get_default_dtype() == torch.double,
        device=device,
    )

    gammatone = diffsptk.GammatoneFilterBankAnalysis(sr, exact=exact).to(device)
    igammatone = diffsptk.GammatoneFilterBankSynthesis(sr, exact=exact).to(device)
    y = igammatone(gammatone(x.unsqueeze(0)))
    assert (x - y).abs().max() < 0.11

    if verbose:
        suffix = "_exact" if exact else ""
        diffsptk.write(f"reconst{suffix}.wav", y.squeeze(), sr)
