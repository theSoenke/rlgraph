# Copyright 2018 The YARL-Project, All Rights Reserved.
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

from yarl.components.memories.memory import Memory
import tensorflow as tf


class ReplayMemory(Memory):
    """
    Implements a standard replay memory to sample randomized batches.
    """

    def __init__(
        self,
        record_space,
        capacity=1000,
        name="",
        scope="replay-memory",
        sub_indexes=None,
        next_states=True,
        episode_semantics=False
    ):
        super(ReplayMemory, self).__init__(record_space, capacity, name, scope, sub_indexes)
        self.next_states = next_states
        self.episode_semantics = episode_semantics

    def create_variables(self):
        # Main memory.
        buffer_variables = self.get_variable(name="replay_buffer", trainable=False, from_space=self.record_space)
        self.build_record_variable_registry(buffer_variables)

        # Main buffer index.
        self.index = self.get_variable(name="index", dtype=int, trainable=False, initializer=0)
        # Number of elements present.
        self.size = self.get_variable(name="size", dtype=int, trainable=False, initializer=0)
        if self.next_states:
            # Next states are not represented as explicit keys in the registry
            # as this would cause extra memory overhead.
            self.states = self.record_space["states"].keys()

        if self.episode_semantics:
            # Only create these if necessary to avoid overhead.
            self.episode = self.get_variable(name="episodes", dtype=int, trainable=False, initializer=0)

    def _computation_insert(self, records):
        num_records = tf.shape(records.keys()[0])
        index = self.read_variable(self.index)
        update_indices = tf.range(start=index, stop=index + num_records) % self.capacity

        # Updates all the necessary sub-variables in the record.
        updates = list()
        self.scatter_update_records(records=records, indices=update_indices, updates=updates)

        # Update indices and size.
        with tf.control_dependencies(updates):
            updates = list()
            updates.append(self.assign_variable(variable=self.index, value=(index + num_records) % self.capacity))
            update_size = tf.minimum(x=(self.read_variable(self.size) + num_records), y=self.capacity)
            updates.append(self.assign_variable(self.size, value=update_size))
            if self.episode_semantics:
                # Update episode indexing.
                pass
                # updates.append()

        # Nothing to return.
        with tf.control_dependencies(updates):
            return tf.no_op()

    def read_records(self, indices):
        """
        Obtains record values for the provided indices.
        Args:
            indices Union[ndarray, tf.Tensor]: Indices to read. Assumed to be not contiguous.

        Returns:
             dict: Record value dict.
        """

        records = dict()
        for name, variable in self.record_registry:
            records[name] = self.read_variable(variable, indices)
        if self.next_states:
            next_indices = (indices + 1) % self.capacity
            next_states = dict()
            # Next states are read via index shift from state variables.
            for state_name in self.states:
                next_states = self.read_variable(self.record_registry[state_name], next_indices)
            records["next_states"] = next_states

        return records

    def _computation_get_records(self, num_records):
        # TODO what modes do we actually need in practice?
        indices = tf.range(start=0, limit=self.read_variable(self.size))

        if self.next_states:
            # Valid indices are non-terminal indices.
            terminal_indices = self.read_variable(self.record_registry['terminal'])
            indices = tf.boolean_mask(tensor=indices, mask=tf.logical_not(x=terminal_indices))

        samples = tf.multinomial(tf.ones_like(indices), num_samples=num_records)
        sampled_indices = indices[tf.cast(samples[0][0], tf.int32)]

        return self.read_records(indices=sampled_indices)

    def _computation_get_sequences(self, num_sequences, sequence_length):
        pass
