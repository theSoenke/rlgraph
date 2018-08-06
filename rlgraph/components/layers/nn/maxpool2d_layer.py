# Copyright 2018 The RLgraph authors. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from rlgraph import get_backend
from rlgraph.utils.initializer import Initializer
from rlgraph.components.layers.nn.nn_layer import NNLayer
from rlgraph.components.layers.nn.activation_functions import get_activation_function

if get_backend() == "tf":
    import tensorflow as tf


class MaxPool2DLayer(NNLayer):
    """
    A max-pooling 2D layer.
    """
    def __init__(self, pool_size, strides, padding="valid", data_format="channels_last", **kwargs):
        """
        Args:
            pool_size (Optional[int,Tuple[int,int]]): An int or tuple of 2 ints (height x width) specifying the
                size of the pooling window. Use a  single integer to specify the same value for all spatial dimensions.
            strides (Union[int,Tuple[int]]): Kernel stride size along height and width axis (or one value
                for both directions).
            padding (str): One of 'valid' or 'same'. Default: 'valid'.
            data_format (str): One of 'channels_last' (default) or 'channels_first'. Specifies which rank (first or
                last) is the color-channel. If the input Space is with batch, the batch always has the first rank.
        """
        super(MaxPool2DLayer, self).__init__(scope=kwargs.pop("scope", "maxpool-2d"), **kwargs)

        self.pool_size = pool_size
        self.strides = strides if isinstance(strides, (tuple, list)) else (strides, strides)
        self.padding = padding
        self.data_format = data_format

        # Create MaxPool layer right away as it doesn't have variables anyway.
        if get_backend() == "tf":
            self.layer = tf.layers.MaxPooling2D(
                pool_size=self.pool_size,
                strides=self.strides,
                padding=self.padding,
                data_format=self.data_format,
            )