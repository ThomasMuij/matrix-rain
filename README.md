# Matrix Rain Terminal Simulation

A customizable terminal-based simulation of the iconic "Matrix rain" effect, written in Python.

## Example of one configuration


![Demo GIF](images/demo1.gif)
![Demo GIF](images/demo2.gif)
This is only 1 example. You can make custom colors, change the characters, difference in speeds, background and much more.
## Installation

### Prerequisites

- **Python 3.8+** is recommended.
- **Optional Dependencies:**
  - [pynput](https://pypi.org/project/pynput/): For keyboard event handling. (recommend)
  - [keyboard](https://pypi.org/project/keyboard/): For keyboard event handling. (might cause some issues)
  - [pathvalidate](https://pypi.org/project/pathvalidate/): For validating file and folder names when saving/loading configurations.

## Setting Up

**Clone the repository:**

```bash
git clone https://github.com/ThomasMuij/matrix-rain.git
cd matrix-rain
```
If you plan to use all the features (keyboard controls and config validation), install:
```bash
pip install pathvalidate
```
Otherwise, if you do not require file/folder validation, you can run without pathvalidate.

Recommended:
```bash
pip install pynput
```
You can also use:
```bash
pip install keyboard
```
## Usage
No keyboard input:
```bash
python matrix_rain.py
```
Using pynput:
```bash
python matrix_pynput.py
```
Using keyboard:
```bash
python matrix_keyboard.py
```
Once running, the matrix rain will animate in your terminal. Use the keyboard controls (see the help screen by pressing the designated key "h") to adjust settings in real time.

## Customization

- **Configuration File**: You can save your settings to a JSON file (in the config_pynput or config_keyboard folder) and load them later. See the on-screen prompts for instructions.

- **Controls:** You can change almost everything using the controls (even the control's keys). To view the controls press "h" while the matrix rain is running. You can also just edit the json files if you want.

## Extra information
- This is my first project and I learned most of the stuff in it while making it. So if you spot any possible issues, bad practices or want me to add a new feautre, feel free to tell me.
- The program was only tested on windows.
- To avoid flickering I am using escape sequences to move the cursor and rewrite the frames instead of clearing the terminal every time. However, if the terminal size is smaller than the animation size, this would cause some prints to remain just keep multiplying. I fixed this by clearing the terminal if it isn't big enough, but this might cause flickering when the animation gets bigger or faster.