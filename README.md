# blackjack-agent
An agent for playing blackjack built using Stochastic Q-Learning.


This is my attempt at creating a blackjack agent using Stochastic Q-Learning and Neural Network techniques. This project was implemented for ESC 704: Stochastic Systems at CSU for the mini-project assignment of the course.


I previously built a similar (but not stochastic) Texas Hold-Em Q-Learning agent along with three of my colleagues for our class project for AI while I was BW. This agent will be significantly more complex and will employ techniques from relevant modern research papers regarding modelling how people play blackjack.


## How does it work?
The agent utilizes card counting and expected payouts to weight actions. Each time the agent chooses to hit or stand, it determines the risks associated with both actions and stochastically chooses the action with less risk. At each game stage, the agent receives a probability distribution generated from the current and prior game state. This distribution is sorted in descending order. The agent then generates a probability and picks the action from the distribution that this probabilty falls into.


For example, if the agent generates the following distribution for the HIT and STAND actions:
```
HIT: 0.78
STAND: 0.22
```
The agent will choose the HIT action with 78% probability and the STAND action with 22% probability.


## Installation Instructions - Linux / Mac
To run the test class on Linux and Mac:
1. Download this repository and extract it's contents to a location on your computer.
2. Open a terminal and navigate to the `[root]/bqa` directory.
3. Create a Python virtual environment by entering `python3 -m venv venv` into your terminal.
4. Activate the virtual environment you just created by typing `. venv/bin/activate` into your terminal.
5. Build and install the bqa package from the setup.py file by typing `python3 setup.py install` into your terminal.
6. Run the game-runner script by typing `game-runner` into your terminal.


The Agent comes with a number of configurable parameters. To see them, type `game-runner --help` into your terminal.


## Installation Instructions - Windows
To run the test class on Windows:
1. Download this repository and extract its contents to a location on your computer.
2. Open a powershell and navigate to the `[root]\bqa` directory.
3. Create a Python virtual environment by entering `python -m venv venv` into powershell.
4. Activate the virtual environment you just created by typing `.\venv\Scripts\activate`. You may need to give your powershell instance access to run third-party scripts. If so, follow the instructions provided by Microsoft [here](https://docs.microsoft.com/en-us/previous-versions//bb613481(v=vs.85)?redirectedfrom=MSDN)
5. Build and install the setup.py file by typing `python setup.py install` in powershell.
6. Run the game-runner script by typing `python bin\game-runner` in powershell from the `[root]\bqa` directory.


**Note**: The `game-runner` script will not directly launch from powershell, hence why you need to launch it with the full command in step 7 above.


## Results
Initial results yield win rates of ~85-90%.
