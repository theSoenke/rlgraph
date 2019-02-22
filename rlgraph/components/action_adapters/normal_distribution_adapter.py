# Copyright 2018/2019 The RLgraph authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from rlgraph import get_backend
from rlgraph.components.action_adapters import ActionAdapter
from rlgraph.utils.decorators import graph_fn


if get_backend() == "tf":
    import tensorflow as tf
elif get_backend() == "pytorch":
    import torch


class NormalDistributionAdapter(ActionAdapter):
    """Action adapter for the Normal distribution"""

    def get_units_and_shape(self, add_units=0, units=None):
        if units is None:
            units = add_units + 2 * self.action_space.flat_dim  # Those two dimensions are the mean and log sd
        # Add moments (2x for each action item).
        if self.action_space.shape == ():
            new_shape = (2,)
        else:
            new_shape = tuple(list(self.action_space.shape[:-1]) + [self.action_space.shape[-1] * 2])
        return units, new_shape

    @graph_fn
    def _graph_fn_get_parameters_log_probs(self, logits):
        parameters = None
        log_probs = None

        if get_backend() == "tf":
            mean, log_sd = tf.split(logits, num_or_size_splits=2, axis=-1)

            # Turn log sd into sd.
            sd = tf.exp(log_sd)

            # Merge again.
            parameters = tf.concat([mean, sd], axis=-1)
            log_probs = tf.concat([tf.log(mean), log_sd], axis=-1)
            parameters._batch_rank = 0
            log_probs._batch_rank = 0

        elif get_backend() == "pytorch":
            mean, log_sd = torch.split(logits, split_size_or_sections=2, dim=1)

            # Turn log sd into sd.
            sd = torch.exp(log_sd)

            parameters = torch.cat([mean, sd], -1)
            log_probs = torch.cat([torch.log(mean), log_sd], -1)

        return parameters, log_probs
