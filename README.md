# blackjack-agent
An agent for playing blackjack built using Stochastic Q-Learning.


This is my attempt at creating a blackjack agent using Stochastic Q-Learning and Neural Network techniques. This project was implemented for ESC 704: Stochastic Systems at CSU for the mini-project assignment of the course.


I previously built a similar (but not stochastic) Texas Hold-Em Q-Learning agent along with three of my colleagues for our class project for AI while I was BW. This agent will be significantly more complex and will employ techniques from relevant modern research papers regarding modelling how people play blackjack.


## Installation Instructions
To run the test class I wrote to utilize the agent follow these instructions:
1. Download this repository and extract it's contents to a location on your computer.
2. Open a terminal and navigate to the `[root]/bqa` directory.
3. Create a Python virtual environment by entering `python -m venv venv` into your terminal.
4. Activate the virtual environment you just created by typing `. venv/bin/activate` into your terminal.
5. Build and install the bqa package from the setup.py file by typing `python setup.py install` into your terminal.
6. Run the game-runner script by typing `game-runner` into your terminal.


The Agent comes with a number of configurable parameters. To see them, type `game-runner --help` into your terminal.


## Results
Initial results yield win rates of ~85-90%.
