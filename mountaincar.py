from tilefeatures import *
from rl import *
import sys
import random
import argparse
import math
turtle = None #placeholder for turtle module

class MountainCar:
    '''Represents the Mountain Car problem.'''
    def __init__(self):
        self.reset()

    def reset(self):
        '''Resets the problem to the initial state.'''                
        self.__pos = -0.5
        self.__vel = 0
        
    def transition(self, action):
        '''Transitions to the next state, depending on the action. Actions 0, 1, and 2 are reverse, neutral, and forward, respectively. Returns the reward from the transition (always -1).'''        
        if self.isTerminal():
            return 0
        
        if action not in range(3):
            raise ValueError("Invalid action: " + str(action))

        direction = action - 1

        self.__pos += self.__vel

        if self.__pos > 0.6:
            self.__pos = 0.6
        elif self.__pos < -1.2:
            self.__pos = -1.2

        self.__vel += direction*(0.001) + math.cos(3*self.__pos)*(-0.0025)

        if self.__vel > 0.07:
            self.__vel = 0.07
        elif self.__vel < -0.07:
            self.__vel = -0.07

        return -1

    def isTerminal(self):
        '''Returns true if the world is in a terminal state (if the car is at the top of the hill).'''
        return self.__pos >= 0.6

    def getState(self):
        '''Returns a tuple containing the position and velocity of the car, in that order.'''
        return (self.__pos, self.__vel)

    def getRanges(self):
        '''Returns a tuple of lists representing the ranges of the two state variables. There are two lists of two elements each, the minimum and maximum value, respectively.'''
        return ([-1.2, 0.6], [-0.07, 0.07])
    
    def __str__(self):
        return "p: " + str(self.__pos) + "v: " + str(self.__vel)

class MountainCarDisplay:
    '''Uses turtle to visualize the Mountain Car problem.'''
    def __init__(self, world):
        '''Takes a MountainCar object and initializes the display.'''
        self.__world = world

        #Create the window
        turtle.setup(800, 400)
        turtle.setworldcoordinates(-1.2, -1.1, 0.6, 1.1)
        turtle.title("Mountain Car")
        turtle.bgcolor(0.4, 0.7, 0.92)
        turtle.tracer(0)

        #Draw the hill
        hillT = turtle.Turtle()
        hillT.hideturtle()
        hillT.penup()
        x = -1.3
        y = math.sin(3*x)
        hillT.goto(x, y)        
        hillT.pendown()
        hillT.pencolor(0, 0.5, 0.1)
        hillT.fillcolor(0, 0.7, 0.1)
        hillT.pensize(4)
        hillT.begin_fill()
        while x < 0.7:
            x += 0.1
            y = math.sin(3*x)
            hillT.goto(x, y)
        hillT.goto(0.7, -1.2)
        hillT.goto(-1.3, -1.2)
        hillT.end_fill()

        #Create the car turtle
        self.__carTurtle = turtle.Turtle()
        self.__carTurtle.shape("circle")
        self.__carTurtle.shapesize(1.5, 1.5, 3)
        self.__carTurtle.fillcolor(1, 0, 0)
        self.__carTurtle.pencolor(0, 0, 0)
        self.__carTurtle.penup()

        self.update()
            
    def update(self):
        '''Updates the display to reflect the current state.'''
        state = self.__world.getState()
        self.__carTurtle.goto(state[0], math.sin(3*state[0])+.1)

        turtle.update()

    def exitOnClick(self):
        turtle.exitonclick()

def main():
    parser = argparse.ArgumentParser(description='Use Sarsa with linear value function approximation to solve the Mountain Car problem.')
    parser.add_argument('output_file', help='file to output the learning data')
    parser.add_argument('-a', '--alpha', type=float, default=0.1, help='the step-size alpha (default: 0.1)')
    parser.add_argument('-e', '--epsilon', type=float, default=0.1, help='the exploration rate epsilon (default: 0.1)')
    parser.add_argument('-g', '--gamma', type=float, default=0.9, help='the discount factor gamma (default: 0.9)')
    parser.add_argument('-t', '--trials', type=int, default=1, help='the number of trials to run (default: 1)')
    parser.add_argument('-p', '--episodes', type=int, default=200, help='the number of episodes per trial (default: 200)')
    parser.add_argument('-m', '--maxsteps', type=int, default=2000, help="the maximum number of steps per episode (default: 2000)")    
    parser.add_argument('-d', '--display', metavar="N", type=int, default=0, help='display every Nth episode (has no effect if TRIALS > 1)')
    parser.add_argument('-n', '--numtilings', type=int, default=5, help='the number of tilings to use')
    parser.add_argument('-s', '--numtiles', metavar="N", type=int, default=9, help='each tiling will divide the space into an NxN grid')

    args = parser.parse_args()
    fout = open(args.output_file, "w")
    world = MountainCar()

    displayError = False
    if args.display > 0:
        try:
            global turtle
            import turtle
        except Exception as ex:
            displayError = True
            print("ERROR: " + str(ex))
            print("WARNING: Unable to initialize the GUI. Display will be disabled.")    
    if args.trials != 1:
        args.display = 0

    if args.display > 0 and not displayError:
        try:
            display = MountainCarDisplay(world)
        except Exception as ex:
            args.display = 0
            print("ERROR: " + str(ex))
            print("WARNING: Unable to initialize the GUI. Display will be disabled.")
    else:
        args.display = 0
        
    avgTotal = [0]*args.episodes
    avgDiscounted = [0]*args.episodes
    avgSteps = [0]*args.episodes
    for trial in range(args.trials):
        if args.trials > 1:
            print("Trial " + str(trial+1), end="")        
        featureGenerator = TileFeatures(world.getRanges(), [args.numtiles, args.numtiles], args.numtilings)
        agent = LinearSarsaLearner(featureGenerator.getNumFeatures(), 3, args.alpha, args.epsilon, args.gamma)
            
        for ep in range(args.episodes):
            if args.display > 0:
                displayEp = ep == 0 or (ep+1)%args.display == 0
            else:
                displayEp = False
                
            if args.trials > 1:
                print(".", end="", flush=True)
            totalR = 0
            discountedR = 0
            discount = 1
            world.reset()
            activeFeatures = featureGenerator.getFeatures(world.getState())
            action = agent.epsilonGreedy(activeFeatures)
            reward = world.transition(action)
            if displayEp:
                display.update()
            totalR += reward
            discountedR += discount*reward            
            step = 1
            while not world.isTerminal() and step < args.maxsteps:
                newFeatures = featureGenerator.getFeatures(world.getState())             
                action = agent.learningStep(activeFeatures, action, reward, newFeatures)
                activeFeatures = newFeatures
                reward = world.transition(action)
                if displayEp:
                    display.update()
                totalR += reward
                discount *= args.gamma
                discountedR += discount*reward
                step += 1
            if world.isTerminal():
                agent.terminalStep(activeFeatures, action, reward)
            else:
                newFeatures = featureGenerator.getFeatures(world.getState())                
                agent.learningStep(activeFeatures, action, reward, newFeatures)
            avgTotal[ep] += totalR
            avgDiscounted[ep] += discountedR
            avgSteps[ep] += step
            if args.trials == 1:
                print("Episode " + str(ep+1) + ": " + str(totalR) + " " + str(discountedR) + " " + str(step))
        if args.trials > 1:
            print("")
           
    for i in range(args.episodes):
        avgStr = str(avgTotal[i]/args.trials) + " " + str(avgDiscounted[i]/args.trials) + " " + str(avgSteps[i]/args.trials)
        fout.write(str(i+1) + " " + avgStr + "\n")
        if args.trials > 1:
            print("Average episode " + str(i) + ": " + avgStr)

    if args.display > 0:
        print("Click the display window to exit")
        display.exitOnClick()
        
if __name__ == "__main__":
    main()
