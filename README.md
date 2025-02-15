# Matrix Rain Terminal Simulation

A customizable terminal-based simulation of the iconic "Matrix rain" effect, written in Python.

## Features

- **Real-time Animation:** Enjoy a continuously updating matrix rain effect directly in your terminal.
- **Configurable Parameters:** Change speed, sequence length, color gradients, and more on the fly.
- **Dynamic Keyboard Controls:** Use intuitive keyboard commands to pause, speed up, slow down, and modify the rain effect while it’s running.
- **Customizable Appearance:** Toggle modes, set custom characters, and adjust background brightness.
- **Save & Load Configurations:** Save your preferred settings to a file and load them later.
- **Automatic Terminal Sizing:** (Optional) Adjusts the matrix size to fit your terminal window.

## Demo

_Add video here (e.g., link to a demo video or GIF showcasing the matrix rain in action)._

## Installation

### Prerequisites

- **Python 3.8+** is recommended.
- **Optional Dependencies:**
  - [pynput](https://pypi.org/project/pynput/): For keyboard event handling. (recommend)
  - [keyboard](https://pypi.org/project/keyboard/): For keyboard event handling. (might cause some issues)
  - [pathvalidate](https://pypi.org/project/pathvalidate/): For validating file and folder names when saving/loading configurations.

### Setting Up

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

Usage
Run the project with:

    python matrix_rain_pynput.py
Or:

    python matrix_rain_keyboard.py
Once running, the matrix rain will animate in your terminal. Use the keyboard controls (see the help screen by pressing the designated key (h)) to adjust settings in real time.

Keyboard Controls

Speed Up / Slow Down: Adjust the animation speed.
Pause/Resume: Temporarily pause the animation.
Toggle Modes: Change how the characters in each sequence are updated.
Adjust Dimensions: Increase or decrease the number of rows and columns.
Change Colors: Switch between different color schemes or create your own.
Save/Load Configuration: Save your current settings or load a configuration file.
Show Help: Display a detailed list of all controls.
For a complete list of controls, press the help key while the program is running.

Customization
Configuration File: You can save your settings to a JSON file (in the config_pynput folder) and load them later. See the on-screen prompts for instructions.
Editing the Code: The project is structured in a single file, but you can refactor it further into modules for better maintainability.
Terminal Size: With the auto-size option enabled, the matrix will adjust to your terminal window dimensions.
Contributing
Contributions are welcome! If you’d like to improve the code or add new features, please follow these steps:

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Commit your changes with clear commit messages.
Open a pull request with a description of your changes.
Before contributing, please ensure your code is clean, well-documented, and adheres to the project’s style.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgements
Inspired by the iconic Matrix movie.
Special thanks to all contributors and the open source community for tools and libraries used in this project.
