# Matrix Rain Terminal Simulation

A customizable terminal-based simulation of the iconic "Matrix rain" effect, written in Python.

## Demo

![Demo GIF](images/demo.gif)

## Installation

### Prerequisites

- **Python 3.8+** is recommended.
- **Optional Dependencies:**
  - [pynput](https://pypi.org/project/pynput/): For keyboard event handling. (recommend)
  - [keyboard](https://pypi.org/project/keyboard/): For keyboard event handling. (might cause some issues)
  - [pathvalidate](https://pypi.org/project/pathvalidate/): For validating file and folder names when saving/loading configurations.

## Setting Up

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/matrix-rain.git
   cd matrix-rain
If you plan to use all the features (keyboard controls and config validation), install:

    pip install pathvalidate
Otherwise, if you do not require file/folder validation, you can run without pathvalidate.

Recommended:

    pip install pynput
You can also use:

    pip install keyboard

## Usage
Run the project with:

    python matrix_rain_pynput.py
Or:

    python matrix_rain_keyboard.py
Once running, the matrix rain will animate in your terminal. Use the keyboard controls (see the help screen by pressing the designated key "h") to adjust settings in real time.

## Customization

- **Configuration File**: You can save your settings to a JSON file (in the config_pynput or config_keyboard folder) and load them later. See the on-screen prompts for instructions.

- **Controls:** You can change almost everything using the controls (even the control's keys). To view the controls press "h" while the matrix rain is running. You can also just edit the json files if you want.

## Extra information
- This is my first project and I learned most of the stuff in it while making it. So if you spot any possible issues, bad practices or want me to add a new feautre, feel free to tell me.
- The program was only tested on windows.
- To avoid flickering I am using escape sequences to move the cursor and rewrite the frames instead of clearing the terminal every time. However, if the terminal size is smaller than the animation size, this would cause some prints to remain just keep multiplying. I fixed this by clearing the terminal if it isn't big enough, but this might cause flickering when the animation gets bigger or faster.