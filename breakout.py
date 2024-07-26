#!/usr/bin/env python3

import os
import re
import json
import argparse

from anthropic import Anthropic

WIDTH = 30
HEIGHT = 20
INPUTS = {'a': 'LEFT', 'd': 'RIGHT', '': 'NONE'}

prompt = """You are a simple game engine for a Breakout-style game. Process the current game state and player input, then return the updated game state. Follow these rules:

1. Game Elements:
   - Paddle: Moves horizontally at the bottom of the screen.
   - Ball: Moves in straight lines, bouncing off walls, paddle, and bricks.
   - Bricks: Arranged at the top of the screen in multiple rows, destroyed when hit by the ball.

2. Game Rules:
   - The ball moves in a straight line until it hits something.
   - When the ball hits a brick:
     * The brick is destroyed and removed from the game.
     * The ball immediately bounces off the brick (reverses its direction).
     * The score increases.
   - The ball bounces off walls and the paddle.
   - If the ball goes below the paddle, the player loses a life.
   - The game ends when all bricks are destroyed or the player runs out of lives.

3. Simplifications:
   - Use integer positions for all elements.
   - The ball always moves at a 45-degree angle (dx and dy are always +1 or -1).
   - The paddle moves 2 units left or right based on input.

4. Collision Detection:
   - Check for collisions in this order: walls, paddle, bricks.
   - If a collision occurs, update the ball's direction immediately before moving to its new position.

5. Input:
   You will receive the current game state in JSON format and the player input (LEFT, RIGHT, or NONE).

6. Output:
   Provide the updated game state in the same JSON format, enclosed in <new_game_state> tags.

Process the game tick as follows:
1. Move the paddle based on input.
2. Check for ball collisions and update its direction if necessary.
3. Move the ball to its new position.
4. Update the game state (remove destroyed bricks, update score, check for lost life).
5. Return the new game state."""

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
    colors = '██▓▒░'
    for brick in state['bricks']:
        x, y = brick['x'], brick['y']
        grid[y][x] = colors[(x + y) % len(colors)]
    
    paddle = state['paddle']
    for x in range(paddle['x'], paddle['x'] + paddle['width']):
        grid[paddle['y']][x] = '▀'
    
    ball = state['ball']
    grid[ball['y']][ball['x']] = '●'
    
    # Add direction indicator
    dx, dy = ball['dx'], ball['dy']
    indicator_x, indicator_y = ball['x'] + dx, ball['y'] + dy
    if 0 <= indicator_x < WIDTH and 0 <= indicator_y < HEIGHT and grid[indicator_y][indicator_x] == ' ':
        if dx > 0 and dy > 0:
            grid[indicator_y][indicator_x] = '↗'
        elif dx > 0 and dy < 0:
            grid[indicator_y][indicator_x] = '↘'
        elif dx < 0 and dy > 0:
            grid[indicator_y][indicator_x] = '↖'
        else:
            grid[indicator_y][indicator_x] = '↙'
    
    print(f"Score: {state['score']} Lives: {state['lives']}")
    print(f"┌{'─' * WIDTH}┐")
    for row in grid[::-1]:
        print(f"│{''.join(row)}│")
    print(f"└{'─' * WIDTH}┘")

def main():
    parser = argparse.ArgumentParser(description='Breakout game engine')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    args = parser.parse_args()

    client = Anthropic()
    state = {
        "paddle": {"x": 11, "y": 1, "width": 8},
        "ball": {"x": 15, "y": 13, "dx": 1, "dy": 1},
        "bricks": [{"x": x, "y": y} for y in range(16, 20) for x in range(0, 30, 2)],
        "score": 0,
        "lives": 3,
    }
    response = None
    while state['lives'] > 0 and state['bricks']:
        os.system('cls' if os.name == 'nt' else 'clear')
        if args.verbose and response:
            print(response + "\n")

        print("Game:")
        render(state)

        while (user_input := input("Enter move ('a'=left, 'd'=right, ''=no movement): ").strip()) not in ["a", "d", ""]:
            print("Invalid input, please enter 'a' or 'd' or ''")

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
        if not (state := parse_state(response)):
            print("Error updating game state. Exiting game.")
            break

    print("Game Over!")
    print(f"Final Score: {state['score']}")

if __name__ == "__main__":
    main()