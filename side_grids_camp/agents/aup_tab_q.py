from ai_safety_gridworlds.environments.shared import safety_game
from collections import defaultdict, namedtuple, Counter
import experiments.environment_helper as environment_helper
import numpy as np


class AUPTabularAgent:
    name = "Tabular AUP"
    pen_epsilon, AUP_epsilon = .2, .9  # chance of choosing greedy action in training
    default = {'N': 150, 'discount': .996, 'rpenalties': 30, 'episodes': 6000}

    def __init__(self, env, N=default['N'], do_state_penalties=False, num_rewards=default['rpenalties'],
                 discount=default['discount'], episodes=default['episodes'], trials=50):
        """Trains using the simulator and e-greedy exploration to determine a greedy policy.

        :param env: Simulator.
        :param N: Maximal impact % the agent can have.
        """
        self.actions = range(env.action_spec().maximum + 1)
        self.probs = [[1.0 / (len(self.actions) - 1) if i != k else 0 for i in self.actions] for k in self.actions]
        self.discount = discount
        self.episodes = episodes
        self.trials = trials
        self.N = N
        self.do_state_penalties = do_state_penalties

        if do_state_penalties:
            self.name = 'Relative Reachability'
            self.penalties = environment_helper.derive_possible_rewards(env)
        else:
            self.penalties = [defaultdict(np.random.random) for _ in range(num_rewards)]
        if len(self.penalties) == 0:
            self.name = 'Vanilla'  # no penalty applied!

        self.train(env)

    def train(self, env):
        self.performance = np.zeros((self.trials, self.episodes / 10))
        self.counts = np.zeros(4)

        for trial in range(self.trials):
            self.penalty_Q = defaultdict(lambda: np.zeros((len(self.penalties), len(self.actions))))
            self.AUP_Q = defaultdict(lambda: np.zeros(len(self.actions)))
            if not self.do_state_penalties:
                self.penalties = [defaultdict(np.random.random) for _ in range(len(self.penalties))]
            self.epsilon = self.pen_epsilon
            for episode in range(self.episodes):
                if episode > 2.0/3 * self.episodes:
                    self.epsilon = self.AUP_epsilon
                time_step = env.reset()
                while not time_step.last():
                    last_board = str(time_step.observation['board'])
                    action = self.behavior_action(last_board)
                    time_step = env.step(action)
                    self.update_greedy(last_board, action, time_step)
                if episode % 10 == 0:
                    _, _, self.performance[trial][episode / 10], _ = environment_helper.run_episode(self, env)
            self.counts[int(self.performance[trial, -1]) + 2] += 1  # -2 goes to idx 0
        env.reset()

    def act(self, obs):
        return self.AUP_Q[str(obs['board'])].argmax()

    def behavior_action(self, board):
        """Returns the e-greedy action for the state board string."""
        greedy = self.AUP_Q[board].argmax()
        if np.random.random() < self.epsilon or len(self.actions) == 1:
            return greedy
        else:  # choose anything else
            return np.random.choice(self.actions, p=self.probs[greedy])

    def get_penalty(self, board, action):
        if len(self.penalties) == 0: return 0
        action_attainable = self.penalty_Q[board][:, action]
        null_attainable = self.penalty_Q[board][:, safety_game.Actions.NOTHING]
        null_sum = sum(abs(null_attainable))

        # Scaled difference between taking action and doing nothing
        return sum(abs(action_attainable - null_attainable)) / (self.N * .01 * null_sum) if (self.N * null_sum) \
            else sum(abs(action_attainable - null_attainable))  # ImpactUnit is 0!

    def update_greedy(self, last_board, action, time_step):
        """Perform TD update on observed reward."""
        learning_rate = 1
        new_board = str(time_step.observation['board'])

        def calculate_update(pen_idx=None):
            """Do the update for the main function (or the penalty function at the given index)."""
            if pen_idx is not None:
                reward = self.penalties[pen_idx](new_board) if self.do_state_penalties \
                    else self.penalties[pen_idx][new_board]
                new_Q, old_Q = self.penalty_Q[new_board][pen_idx].max(), \
                               self.penalty_Q[last_board][pen_idx, action]
            else:
                reward = time_step.reward - self.get_penalty(last_board, action)
                new_Q, old_Q = self.AUP_Q[new_board].max(), self.AUP_Q[last_board][action]
            return learning_rate * (reward + self.discount * new_Q - old_Q)

        # Learn the other reward functions, too
        for pen_idx in range(len(self.penalties)):
            self.penalty_Q[last_board][pen_idx, action] += calculate_update(pen_idx)
        if self.do_state_penalties:
            self.penalty_Q[last_board][:, action] = np.clip(self.penalty_Q[last_board][:, action],
                                                            0, 1)
        self.AUP_Q[last_board][action] += calculate_update()
