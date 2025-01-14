import sys
import os
import csv

# Get the parent directory (one level up)
main_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(main_directory)

from tetris_engine import Tetris
from agent_dqn import Agent, QNetwork
import time
import numpy as np
import pygame
import torch
from torch.utils.tensorboard import SummaryWriter

seed = 1
env = Tetris(10, 20, seed)
agent = Agent(env.state_size, seed=seed)


pygame.init()
width, height = 250, 625
screen = pygame.display.set_mode((width, height))

# model_name = "DQN_server_25_000_3"
model_name = "DQN_server_2_000_final"
model_path = f"DQN/models/{model_name}.pt"

model = QNetwork(env.state_size)
model.load_state_dict(
    torch.load(model_path, map_location=torch.device("cpu"))
)  # Modified line
model.eval()

max_episodes = 125
episodes = []
rewards = []
tetris_clear_list = []
current_max = 0
interval_reward = []
highscore = 0
exit_program = False

log_evaluation = True
log_name = "DQN_test"
framerate = 10
run_hold = True
print_interval = 1
steps = 0
max_steps = 5_000


if log_evaluation:
    log_dir = "./DQN/evaluation/" + log_name
    writer = SummaryWriter(log_dir=log_dir)


def logging():
    writer.add_scalar("Tetris clears:", env.tetris_amount, episode)
    writer.add_scalar("Total Reward", total_reward, episode)
    writer.add_scalar("Steps per Episode:", steps, episode)


def timer(start_time, end_time):
    end_time = time.time()
    elapsed_time_seconds = end_time - start_time
    if elapsed_time_seconds < 60:
        seconds = round(elapsed_time_seconds, 2)
        minutes = 0
    else:
        minutes = int(elapsed_time_seconds // 60)
        seconds = int(elapsed_time_seconds % 60)

    return (minutes, seconds)


print("Game is running")

for episode in range(max_episodes):
    current_state = env.reset()
    done = False
    total_reward = 0
    env.tetris_amount = 0
    start_time = time.time()
    steps = 0
    env.types_of_clears = {"1": 0, "2": 0, "3": 0, "4": 0}

    while not done and steps < max_steps:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    env.toggle_render()  # Toggle render state with 'r'
                if event.key == pygame.K_q:
                    exit_program = True
                if event.type == pygame.QUIT:
                    exit_program = True

        if exit_program:
            break

        if env.render_enabled:
            env.render(total_reward, framerate)

        if run_hold:
            next_states = env.merge_next_states()
        else:
            next_states = env.get_next_states(env.shape, env.anchor, False)

        # If the dictionary is empty, meaning the game is over
        if not next_states:
            break

        states = list(next_states.values())
        # Tell the agent to choose the best possible state
        best_state = agent.act(states=states, model=model, use_epsilon=False)

        # Grab the best tetromino position and its rotation chosen by the agent
        best_action = None
        for action, state in next_states.items():
            if (best_state == state).all():
                best_action = action
                break

        reward, done = env.step(best_action)
        total_reward += reward

        current_state = next_states[best_action]

        if steps % 500 == 0:
            print(f"Steps: {str(steps)}")
            print(f"Current Reward: {str(total_reward)}")
            print(f"Number of tetris: {str(env.tetris_clear)}")
            print(f"Clear list: {env.types_of_clears}")

        steps += 1

    end_time = time.time()

    if log_evaluation:
        logging()

    if exit_program:
        break

    episodes.append(episode)
    rewards.append(total_reward)
    tetris_clear_list.append(env.tetris_clear)

    if total_reward > highscore:
        highscore = total_reward

    # Print training data
    if episode % print_interval == 0:
        print("-" * 30)
        print(f"Running episode {str(episode + 1)}")
        print(f"Mean reward:  {str(np.mean(rewards[-print_interval:]))}")
        print(f"Round Highscore: {str(max(rewards[-print_interval:]))}")
        print(f"Training Highscore: {str(highscore)}")
        print(
            f"Round 'tetris-clear' highscore:{str(max(tetris_clear_list[-print_interval:]))}"
        )
        print(f"'tetris-clear' highscore:{str(max(tetris_clear_list))}")
        print(
            f"episodetime: {timer(start_time, end_time)[0]} minutes, {timer(start_time, end_time)[1]} seconds"
        )

    with open("DQN/evaluation/eval_test.csv", "a", newline="") as file:
        writer_csv = csv.writer(file)
        writer_csv.writerow(
            [
                total_reward,
                env.types_of_clears["1"],
                env.types_of_clears["2"],
                env.types_of_clears["3"],
                env.types_of_clears["4"],
            ]
        )

    env.seed += 1

if log_evaluation:
    writer.close()

print(f"Game score: {str(total_reward)}")
print(f"Game tetris: {str(env.tetris_clear)}")
print(f"Mean score:{str(np.mean(rewards))} of {str(episode)} episode")
print(f"Std score:{str(np.std(rewards))} of {str(episode)} episode")
print(f"Highscore: {str(highscore)}")
print(f"'tetris-clear' highscore: {str(max(tetris_clear_list))}")


pygame.quit()
