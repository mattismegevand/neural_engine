#!/usr/bin/env python3

import os
import re
import json
import argparse

from anthropic import Anthropic

WIDTH = 20
HEIGHT = 15
INPUTS = {'w': 'UP', 's': 'DOWN', 'a': 'LEFT', 'd': 'RIGHT', '': 'NONE'}

prompt = """You are a simple game engine for a Snake game. Process the current game state and player input, then return the updated game state. Follow these rules:

1. Game Elements:
   - Snake: A series of connected segments, with the head leading the movement.
   - Food: A single item that appears randomly on the screen.

2. Game Rules:
   - The snake moves in the direction of the last input.
   - If the snake eats food, it grows by one segment and new food appears.
   - If the snake hits a wall or itself, the game ends.
   - The score increases each time the snake eats food.

3. Simplifications:
   - Use integer positions for all elements.
   - The snake moves one unit at a time in the input direction.

4. Collision Detection:
   - Check for collisions with walls, food, and snake body.

5. Input:
   You will receive the current game state in JSON format and the player input (UP, DOWN, LEFT, RIGHT, or NONE).

6. Output:
   Provide the updated game state in the same JSON format, enclosed in <new_game_state> tags.

Process the game tick as follows:
1. Move the snake based on input.
2. Check for collisions and update the game state accordingly.
3. If food is eaten, grow the snake and spawn new food.
4. Return the new game state."""

def get_prompt(state, player_input):
    return f"{prompt}\n<game_state>\n{json.dumps(state)}\n</game_state>\n<player_input>\n{player_input}\n</player_input>"

def parse_state(response):
    match = re.search(r"<new_game_state>(.*?)</new_game_state>", response, re.DOTALL)
    if match:
        json_state = match.group(1).strip()
        return json.loads(json_state)
    return None

def render(state):
    grid = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]
    
    for segment in state['snake']:
        x, y = segment['x'], segment['y']
        grid[y][x] = '■'
    
    head = state['snake'][0]
    grid[head['y']][head['x']] = '●'
    
    food = state['food']
    grid[food['y']][food['x']] = '★'
    
    print(f"Score: {state['score']}")
    print(f"┌{'─' * WIDTH}┐")
    for row in grid:
        print(f"│{''.join(row)}│")
    print(f"└{'─' * WIDTH}┘")

def main():
    parser = argparse.ArgumentParser(description='Snake game engine')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    args = parser.parse_args()

    client = Anthropic()
    state = {
        "snake": [{"x": 10, "y": 7}, {"x": 9, "y": 7}, {"x": 8, "y": 7}],
        "food": {"x": 15, "y": 7},
        "direction": "RIGHT",
        "score": 0,
    }
    response = None

    while not state.get('game_over', False):
        os.system('cls' if os.name == 'nt' else 'clear')
        if args.verbose and response:
            print(response + "\n")

        print("Game:")
        render(state)

        while (user_input := input("Enter move ('w'=up, 's'=down, 'a'=left, 'd'=right, ''=no change): ").strip()) not in ["w", "s", "a", "d", ""]:
            print("Invalid input, please enter 'w', 's', 'a', 'd' or ''")

        prompt = get_prompt(state, INPUTS[user_input])
        message = client.messages.create(
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt,
            }],
            model="claude-3-5-sonnet-20240620",
        )

        response = message.content[0].text
        if (state := parse_state(response)):
            game_over = state.get('game_over', False)
        else:
            print("Error updating game state. Exiting game.")
            break

    print("Game Over!")
    print(f"Final Score: {state['score']}")

if __name__ == "__main__":
    main()