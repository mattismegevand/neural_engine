#!/usr/bin/env python3

import os
import re
import json
import argparse
from anthropic import Anthropic
from functools import partial

WIDTH = 9
HEIGHT = 11
INPUTS = { 'a': 'LEFT', 'd': 'RIGHT', '': 'NONE' }

prompt = """You are acting as a game engine for a Breakout-style game. Your task is to process the current game state and player input, then return the updated game state. Follow these instructions carefully:

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
b) Check for collisions:
   - If the ball hits a wall, reverse its x-velocity.
   - If the ball hits the ceiling, reverse its y-velocity.
   - If the ball hits the paddle, reverse its y-velocity and adjust x-velocity based on where it hit the paddle:
     * If it hits the left third of the paddle, set dx to -1
     * If it hits the middle third, keep the current dx
     * If it hits the right third, set dx to 1
   - If the ball hits a brick, destroy the brick, increase the score, and reverse the ball's y-velocity.
c) Update the ball position based on its velocity.
d) If the ball goes below the paddle, decrease lives by 1.
e) Check if the game has ended (all bricks destroyed or no lives left).

5. Outputting the New Game State:
Provide the updated game state in the same format as the input, enclosed in <new_game_state> tags. Include a brief explanation of what changed in the game state, enclosed in <explanation> tags.

Remember to process the game mechanics step-by-step and ensure that all aspects of the game state are updated correctly. If you're unsure about any calculations or need to break down complex logic, use <thinking> tags to show your reasoning before providing the final output."""

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
    bx, by, dx, dy = ball['x'], ball['y'], ball['dx'], ball['dy']
    grid[by][bx] = 'O'
    if 0 <= by+dy < HEIGHT and 0 <= bx+dx < WIDTH:
        grid[by+dy][bx+dx] = '.'

    print(f"Score: {state['score']} Lives: {state['lives']}")
    print(f"+{'-' * WIDTH}+")
    for row in grid[::-1]:
        print(f"|{''.join(row)}|")
    print(f"+{'-' * WIDTH}+")

def llm_render(client, state):
    render_prompt = f"""Given the following game state for a Breakout-style game, create an ASCII representation of the game board:

Game State:
{json.dumps(state, indent=2)}

Rules for ASCII representation:
- Use a 9x11 grid (WIDTH x HEIGHT)
- Represent bricks with '#'
- Represent the paddle with '='
- Represent the ball with 'O'
- Use empty spaces for empty cells
- Show the score and lives at the top
- Enclose the grid with '+' and '-' characters

Please provide only the ASCII representation without any additional explanation."""

    message = client.messages.create(
        max_tokens=1024,
        temperature=0.0,
        messages=[{
            "role": "user",
            "content": render_prompt,
        }],
        model="claude-3-opus-20240229",
    )

    ascii_representation = message.content[0].text.strip()
    print(ascii_representation)

def main():
    parser = argparse.ArgumentParser(description='Breakout game engine')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    parser.add_argument('-r', '--render', choices=['render', 'llm_render'], default='render', help='Choose the rendering method')
    parser.add_argument('-t', '--temperature', type=float, default=0.0, help='Set the temperature for text generation')
    args = parser.parse_args()

    client = Anthropic()
    render_func = render if args.render == 'render' else partial(llm_render, client=client)
    state = {
        "paddle": {"x": [3, 4, 5]},
        "ball": {"x": 4, "y": 2, "dx": 1, "dy": 1},
        "bricks": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "score": 0,
        "lives": 3,
    }
    response = None
    while state['lives'] > 0:
        os.system('cls' if os.name == 'nt' else 'clear')
        if args.verbose and response:
            print(response + "\n")

        print("Game:")
        render_func(state=state)

        while (user_input := input("Enter move ('a'=left, 'd'=right, ''=no movement): ").strip()) not in ["a", "d", ""]:
            print("Invalid input, please enter 'a' or 'd' or ''")

        prompt = get_prompt(state, INPUTS[user_input])
        message = client.messages.create(
            max_tokens=2048,
            temperature=args.temperature,
            messages=[{
                "role": "user",
                "content": prompt,
            }],
            model="claude-3-opus-20240229",
        )

        response = message.content[0].text
        if not (state := parse_state(response)):
            print("Error updating game state. Exiting game.")
            break

    print("Game Over!")
    print(f"Final Score: {state['score']}")

if __name__ == "__main__":
    main()