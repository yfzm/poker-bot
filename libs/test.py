from game import *
import sys
import os
import time

# action is str like 'BET' 'CALL', playerPos is an integer which show the pos of a player
# body is an dict obj.
def checkHook(game, action, playerPos, body):
    print("action: {}, player: {}, body: {} \n".format(action, playerPos, body))

a = Game(6)

a.setOb(checkHook)

a.setPlayer(0, 500)
a.setPlayer(1, 500)
a.setPlayer(2, 500)

a.setReady(0) # btn and utg
a.setReady(1) # sb
a.setReady(2) # bb

a.start()

# utg call
a.pcall(0)

# sb call
a.pcall(1)

# FLOP
a.praise(1, 40)
a.pcall(2)
a.pcall(0)

# TURN
a.pallin(1)
a.pcall(2) # will be allin
a.pcall(0) # wiil be allin

# RIVER

print('end')
time.sleep(1)
os._exit(status=0)