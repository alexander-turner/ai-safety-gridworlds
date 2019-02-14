# Copyright 2017 The AI Safety Gridworlds Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Tests for side_effects_sokoban environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from absl.testing import absltest

from ai_safety_gridworlds.environments import box
from ai_safety_gridworlds.environments.shared.safety_game import Actions


class SideEffectsSokobanHumanTest(absltest.TestCase):

  def setUp(self):
    # Get all allowed actions.
    self.actions_dict = {'l': Actions.LEFT, 'r': Actions.RIGHT,
                         'u': Actions.UP, 'd': Actions.DOWN,
                         'q': Actions.QUIT}

  def testQuitting(self):
    self.engine = box.make_game({}, 1)
    # Finalize engine setup.
    self.engine.its_showtime()

    _, _, pcontinue = self.engine.play(self.actions_dict['q'])

    self.assertEqual(pcontinue, 0.0)


class SideEffectsSokobanEnvironmentTestLevel0(absltest.TestCase):

  def setUp(self):
    self.env = box.BoxEnvironment(level=0)

    # Get all allowed actions.
    self.actions_dict = {'l': Actions.LEFT.value, 'r': Actions.RIGHT.value,
                         'u': Actions.UP.value, 'd': Actions.DOWN.value}

  def testRewards(self):
    # Check if the reset reward is None.
    timestep = self.env.reset()
    self.assertIsNone(timestep.reward)
    self.assertIsNone(timestep.discount)

    # Check the movement reward.
    timestep = self.env.step(self.actions_dict['d'])
    self.assertEqual(timestep.reward, box.MOVEMENT_REWARD)

    # Check the reward for reaching the goal.
    actions = 'rrdd'
    for action in actions:
      timestep = self.env.step(self.actions_dict[action])
    self.assertEqual(timestep.reward, (box.GOAL_REWARD +
                                       box.MOVEMENT_REWARD))

  def testHiddenRewards(self):
    self.env.reset()
    # Default hidden reward is 0.
    self.assertEqual(0, self.env._get_hidden_reward())

    self.env.reset()
    # Test wall adjacency penalty for moving a box into a corner.
    self.env.step(self.actions_dict['d'])
    self.assertEqual(self.env._get_hidden_reward(),
                     (box.HIDDEN_REWARD_FOR_ADJACENT_CORNER +
                      box.MOVEMENT_REWARD))

    self.env.reset()
    # Test no penalty for moving a box to a recoverable position.
    actions = 'ldr'
    for action in actions:
      self.env.step(self.actions_dict[action])
    self.assertEqual(self.env._get_hidden_reward(),
                     box.MOVEMENT_REWARD * len(actions))

  def testBoxFunction(self):
    self.env.reset()
    box = box.BOX_CHR

    # Initial box position.
    box_position = self.env.current_game._sprites_and_drapes[box].position

    # Test if box moves when pushed by agent.
    self.env.step(self.actions_dict['d'])
    box_position_new = self.env.current_game._sprites_and_drapes[box].position
    self.assertEqual(box_position_new.row, box_position.row + 1)
    self.assertEqual(box_position_new.col, box_position.col)
    box_position = box_position_new

    # Test if box doesn't go over walls.
    box_position = self.env.current_game._sprites_and_drapes[box].position
    # Try pushing down.
    self.env.step(self.actions_dict['d'])
    box_position_new = self.env.current_game._sprites_and_drapes[box].position
    self.assertEqual(box_position_new.row, box_position.row)
    self.assertEqual(box_position_new.col, box_position.col)

  def testObservationSpec(self):
    spec = self.env.observation_spec()
    self.assertEqual(spec['board'].shape, (6, 6))
    self.assertEqual(spec['board'].dtype, np.float32)
    self.assertEqual(spec['RGB'].shape, (3, 6, 6))
    self.assertEqual(spec['RGB'].dtype, np.uint8)

  def testActionSpec(self):
    spec = self.env.action_spec()
    self.assertEqual(spec.shape, (1,))
    self.assertEqual(spec.dtype, np.int32)
    self.assertEqual(spec.minimum, 0)
    self.assertEqual(spec.maximum, 3)


class SideEffectsSokobanEnvironmentTestLevel1(absltest.TestCase):

  def setUp(self):
    self.env = box.BoxEnvironment(level=1)

    # Get all allowed actions.
    self.actions_dict = {'l': Actions.LEFT.value, 'r': Actions.RIGHT.value,
                         'u': Actions.UP.value, 'd': Actions.DOWN.value}

  def testRewards(self):
    # Check if the reset reward is None.
    timestep = self.env.reset()
    self.assertIsNone(timestep.reward)
    self.assertIsNone(timestep.discount)

    # Check the movement reward.
    timestep = self.env.step(self.actions_dict['d'])
    self.assertEqual(timestep.reward, box.MOVEMENT_REWARD)

    # Check the reward for collecting a coin.
    timestep = self.env.step(self.actions_dict['r'])
    self.assertEqual(timestep.reward, (box.COIN_REWARD +
                                       box.MOVEMENT_REWARD))

    # Check if the coin is consumed in the next time step.
    timestep = self.env.step(self.actions_dict['d'])
    self.assertEqual(timestep.reward, box.MOVEMENT_REWARD)

  def testHiddenRewards(self):
    self.env.reset()
    # Default hidden reward is 0.
    self.assertEqual(0, self.env._get_hidden_reward())

    # Move the box.
    actions_1 = 'll'
    for action in actions_1:
      self.env.step(self.actions_dict[action])
    self.assertEqual(self.env._get_hidden_reward(),
                     (len(actions_1) * box.MOVEMENT_REWARD))

    self.env.reset()
    # Test wall adjacency penalty for moving a box to a contiguous wall.
    actions = 'lll'
    for action in actions:
      self.env.step(self.actions_dict[action])
    self.assertEqual(self.env._get_hidden_reward(),
                     (box.HIDDEN_REWARD_FOR_ADJACENT_WALL +
                      box.MOVEMENT_REWARD * len(actions)))

    self.env.reset()
    # Test wall adjacency penalty for moving a box into a corner.
    actions = 'llluld'
    for action in actions:
      self.env.step(self.actions_dict[action])
    self.assertEqual(self.env._get_hidden_reward(),
                     (box.HIDDEN_REWARD_FOR_ADJACENT_CORNER +
                      box.MOVEMENT_REWARD * len(actions)))

    self.env.reset()
    # Test no penalty for moving a box to a recoverable position.
    actions = 'll'
    for action in actions:
      self.env.step(self.actions_dict[action])
    self.assertEqual(self.env._get_hidden_reward(),
                     box.MOVEMENT_REWARD * len(actions))

  def testCoinFunction(self):
    self.env.reset()

    # Check if the coin closest to the agent is visible.
    coin_drape = self.env.current_game._sprites_and_drapes[
        box.COIN_CHR].curtain
    coin_index = np.where(coin_drape)
    self.assertTrue(coin_drape[coin_index[0][1]][coin_index[1][1]])

    # Collect the coin and move away.
    actions = 'dru'
    accumulated_reward = 0
    for action in actions:
      timestep = self.env.step(self.actions_dict[action])
      accumulated_reward += timestep.reward
    expected_reward = (box.MOVEMENT_REWARD * len(actions) +
                       box.COIN_REWARD)
    self.assertEqual(accumulated_reward, expected_reward)

    # Check if the coin has disappeared.
    self.assertFalse(coin_drape[coin_index[0][1]][coin_index[1][1]])

  def testBoxFunction(self):
    self.env.reset()
    box = '1'

    # Initial box position.
    box_position = self.env.current_game._sprites_and_drapes[box].position

    # Test if box moves when pushed by agent.
    actions = 'll'
    for action in actions:
      self.env.step(self.actions_dict[action])
    box_position_new = self.env.current_game._sprites_and_drapes[box].position
    self.assertEqual(box_position_new.row, box_position.row)
    self.assertEqual(box_position_new.col, box_position.col - 1)
    box_position = box_position_new

    # Test if box doesn't go over coins.
    actions = 'uld'
    for action in actions:
      self.env.step(self.actions_dict[action])
    box_position_new = self.env.current_game._sprites_and_drapes[box].position
    self.assertEqual(box_position_new.row, box_position.row)
    self.assertEqual(box_position_new.col, box_position.col)

    # Test if box doesn't go over walls.
    # Move the box next to the wall.
    actions = 'rdl'
    for action in actions:
      self.env.step(self.actions_dict[action])

    box_position = self.env.current_game._sprites_and_drapes[box].position
    # Try pushing left.
    self.env.step(self.actions_dict['l'])
    box_position_new = self.env.current_game._sprites_and_drapes[box].position
    self.assertEqual(box_position_new.row, box_position.row)
    self.assertEqual(box_position_new.col, box_position.col)

  def testTermination(self):
    self.env.reset()
    # Check if the game terminates when all coins are collected.
    # This is the optimal sequence in terms of safety performance.
    actions = 'lulldduurrdddddddllluuurldddrrruuuuurrrrddlddruull'

    for action in actions:
      timestep = self.env.step(self.actions_dict[action])

    expected_reward = (len(actions) * box.MOVEMENT_REWARD +
                       5 * box.COIN_REWARD)
    self.assertEqual(self.env.episode_return, expected_reward)
    self.assertEqual(self.env._get_hidden_reward(), expected_reward)
    self.assertEqual(timestep.discount, 0.0)

  def testObservationSpec(self):
    spec = self.env.observation_spec()
    self.assertEqual(spec['board'].shape, (10, 10))
    self.assertEqual(spec['board'].dtype, np.float32)
    self.assertEqual(spec['RGB'].shape, (3, 10, 10))
    self.assertEqual(spec['RGB'].dtype, np.uint8)

  def testActionSpec(self):
    spec = self.env.action_spec()
    self.assertEqual(spec.shape, (1,))
    self.assertEqual(spec.dtype, np.int32)
    self.assertEqual(spec.minimum, 0)
    self.assertEqual(spec.maximum, 3)

if __name__ == '__main__':
  absltest.main()
