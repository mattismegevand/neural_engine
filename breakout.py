#!/usr/bin/env python3

import os
import re
import sys
import json
from anthropic import Anthropic

WIDTH = 9
HEIGHT = 11
INPUTS = { 'a': 'LEFT', 'd': 'RIGHT', '': 'NONE' }

prompt = """
You are acting as a game engine for a Breakout-style game. Your task is to process the current game state and player input, then return the updated game state. Follow these instructions carefully:

1. Game Rules and Mechanics:
- The game consists of a paddle, a ball, and bricks.
- The paddle moves horizontally at the bottom of the screen.
- The ball bounces off the paddle, walls, and bricks.
- When the ball hits a brick, the brick is destroyed.
- If the ball goes below the paddle, the player loses a life.
- The game ends when all bricks are destroyed or the player runs out of lives.
- Size of the grid is 9 by 11, (0, 0) being the lower left corner and (8, 10) being the top right corner.
- Bricks are located at the top of the grid row 10.
- In case user try to move paddle beyond screen width paddle[x][0] <= 0 or paddle[x][-1] >= 9, paddle will not move.

2. Interpreting the Game State:
You will receive the current game state in the following format:
<game_state>
{{GAME_STATE}}
</game_state>

The game state includes:
- Paddle position (x-coordinate)
- Ball position (x and y coordinates)
- Ball velocity (dx and dy)
- Brick layout (a grid of 0s and 1s, where 1 represents an intact brick)
- Score
- Lives remaining

3. Processing Player Input:
You will receive the player's input in the following format:
<player_input>
{{PLAYER_INPUT}}
</player_input>

The player input will be one of:
- "LEFT": Move the paddle left
- "RIGHT": Move the paddle right
- "NONE": No movement

4. Updating the Game State:
Based on the current game state and player input, update the game state as follows:
a) Move the paddle according to the player input.
b) Update the ball position based on its velocity.
c) Check for collisions:
   - If the ball hits a wall, reverse its x-velocity.
   - If the ball hits the ceiling, reverse its y-velocity.
   - If the ball hits the paddle, reverse its y-velocity and adjust x-velocity based on where it hit the paddle.
   - If the ball hits a brick, destroy the brick, increase the score, and reverse the ball's y-velocity.
d) If the ball goes below the paddle, decrease lives by 1.
e) Check if the game has ended (all bricks destroyed or no lives left).

5. Outputting the New Game State:
Provide the updated game state in the same format as the input, enclosed in <new_game_state> tags. Include a brief explanation of what changed in the game state, enclosed in <explanation> tags.

Remember to process the game mechanics step-by-step and ensure that all aspects of the game state are updated correctly. If you're unsure about any calculations or need to break down complex logic, use <thinking> tags to show your reasoning before providing the final output.
"""

def get_prompt(state, player_input):
    return f"{prompt}\n<game_state>\n{json.dumps(state)}\n</game_state>\n<player_input>\n{player_input}\n</player_input>"

def parse_state(response):
    match = re.search(r"<new_game_state>(.*?)</new_game_state>", response, re.DOTALL)
    json_state = match.group(1).strip()
    return json.loads(json_state)

def render(state):
    grid = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for y, row in enumerate(state['bricks']):
        for x, brick in enumerate(row):
            if brick == 1:
                grid[HEIGHT - y - 1][x] = '#'
    for x in state['paddle']['x']:
        grid[1][x] = '='
    ball = state['ball']
    grid[ball['y']][ball['x']] = 'O'

    print(f"Score: {state['score']} Lives: {state['lives']}")
    print(f"+{'-' * WIDTH}+")
    for row in grid[::-1]:
        print(f"|{''.join(row)}|")
    print(f"+{'-' * WIDTH}+")

def main():
    verbose = sys.argv[1].lower() in ["-v", "--verbose"] if len(sys.argv) > 1 else False
    client = Anthropic()
    state = {
        "paddle": {"x": [3, 4, 5]},
        "ball": {"x": 4, "y": 2, "dx": 0, "dy": 1},
        "bricks": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "score": 0,
        "lives": 3,
    }

    while state['lives'] > 0:
        if verbose:
            print(response)
        else:
            os.system('cls' if os.name == 'nt' else 'clear')

        print("Game:")
        render(state)

        while (user_input := input("Enter move ('a'=left, 'd'=right, ''=no movement): ").strip()) not in ["a", "d", ""]:
            print("Invalid input, please enter 'a' or 'd' or ''")

        prompt = get_prompt(state, INPUTS[user_input])
        message = client.messages.create(
            max_tokens=2048,
            temperature=0.0,
            messages=[{
                "role": "user",
                "content": prompt,
            }],
            model="claude-3-opus-20240229",
        )

        response = message.content[0].text
        if verbose:
            print(response)
        new_state = parse_state(response)

        if new_state:
            state = new_state
        else:
            print("Error updating game state. Exiting game.")
            break

    print("Game Over!")
    print(f"Final Score: {state['score']}")

if __name__ == "__main__":
    main()