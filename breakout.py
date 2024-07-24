#!/usr/bin/env python3

import os
import re
from anthropic import Anthropic

prompt = """
You are a Breakout game engine. Process the game state and user input to generate the next state.

Game state format:
ball_x,ball_y|ball_dx,ball_dy|paddle_x|bricks|score|lives

Where:
- ball_x and ball_y are the ball's coordinates (integers from 0 to 9)
- ball_dx and ball_dy are the ball's velocity components (integers: -1, 0, or 1)
- paddle_x is the paddle's left edge x-coordinate (integer from 1 to 8)
- bricks is a string of 9 '0's and '1's representing destroyed and present bricks respectively
- score and lives are integers
- the game area is 10 units wide (0 to 9) and 10 units high (0 to 9)
- the paddle is 3 units wide and represented by 'P'
- the ball is represented by a 'o'
- there is one row of 9 bricks at the top of the game area (y=0) bricks are '1'
- (0,0) is top-left (10,9) is bottom-right

Example:
Input: 5,7|0,-1|5|111111111|0|3
User input: d

Output:
5,6|0,-1|5|111111111|0|3
┌──────────┐
│1111111111│
│          │
│          │
│          │
│          │
│          │
│    o     │
│          │
│   PPP    │
└──────────┘

Current game state:
"""

def get_prompt(b_pos, b_d, p_x, bricks, score, lives):
    return f"{prompt}{b_pos[0]},{b_pos[1]}|{b_d[0]},{b_d[1]}|{p_x}|{bricks}|{score}|{lives}\nFOLLOW EXAMPLE FORMAT!!!"

def parse_response(response):
    state_regex = r"(\d+),(\d+)\|(-?\d+),(-?\d+)\|(\d+)\|([01]{9})\|(\d+)\|(\d+)"
    match = re.search(state_regex, response)
    if match:
        ball_x, ball_y, ball_dx, ball_dy, paddle_x, bricks, score, lives = match.groups()
        return (int(ball_x), int(ball_y)), (int(ball_dx), int(ball_dy)), int(paddle_x), bricks, int(score), int(lives)
    return None

def render_game(response):
    game_area = re.search(r"┌.*┘", response, re.DOTALL).group(0)
    print(game_area)

def main():
    client = Anthropic()
    b_pos = (5, 7)
    b_d = (0, -1)
    p_x = 5
    bricks = "1" * 9
    score = 0
    lives = 3

    prompt = get_prompt(b_pos, b_d, p_x, bricks, score, lives)
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Game:")
    render_game(prompt)
    while lives > 0:
        while (user_input := input("Enter move ('a'=left, 'd'=right, ''=no movement): ").strip()) not in ["a", "d", ""]:
            print("Invalid input, please enter 'a' or 'd' or ''")

        prompt += f"\nUser input: '{user_input}'\nOutput:"

        message = client.messages.create(
            max_tokens=2048,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt,
            }],
            model="claude-3-opus-20240229",
        )

        response = message.content[0].text

        parsed_state = parse_response(response)
        if parsed_state:
            b_pos, b_d, p_x, bricks, score, lives = parsed_state
            os.system('cls' if os.name == 'nt' else 'clear')
            render_game(response)
            prompt = get_prompt(b_pos, b_d, p_x, bricks, score, lives)
        else:
            print("Error parsing response. Exiting game.")
            break

if __name__ == "__main__":
    main()
