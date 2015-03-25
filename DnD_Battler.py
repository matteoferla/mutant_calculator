__author__ = "Matteo"
__copyright__ = "paiment in beer"
__email__ = "matteo.ferla@gmail.com"
__date__ = '25/03/15'

class Dice:
    def __init__(self, bonus=0, dice=20):
        self.bonus = bonus
        self.dice = dice

    def roll(self):
        return random.randint(1, self.dice) + self.bonus


class Creature:
    def __init__(self, name, alignment="good", ac=10, initiative_bonus=0, hp=1, attack_bonus=0, damage_bonus=0, damage_dice=6,
                 healing_spells=0, healing_dice=4, healing_bonus=0):
        self.name = name
        self.ac = ac
        self.starting_hp = hp
        self.hp = hp
        self.initiative = Dice(initiative_bonus, 20)
        self.attack = Dice(attack_bonus, 20)
        self.damage = Dice(damage_bonus, damage_dice)
        self.starting_healing_spells = healing_spells
        self.healing_spells = healing_spells
        self.healing = Dice(healing_bonus,healing_dice)
        self.alignment=alignment

    def __str__(self):
        return self.name + ": {team="+self.alignment+"; current hp="+str(self.hp)+" (from "+str(self.starting_hp)+"); healing spells left="+str(self.healing_spells)+" (from "+str(self.starting_healing_spells)+");}"

    def hit(self, opponent):
        swing = self.attack.roll()
        if swing >= opponent.ac:
            opponent.wound(self.damage.roll())

    def wound(self, points, verbose=0):
        self.hp -= points
        if verbose: print(self.name + ' took ' + str(points) + ' of damage. Now on ' + str(self.hp) + ' hp.')

    def heal(self, points, verbose=0):
        self.hp += points
        if verbose: print(self.name + ' was healed by ' + str(points) + '. Now on ' + str(self.hp) + ' hp.')

    def cast_healing(self, verbose=0):
        if self.healing_spells > 0:
            self.heal(self.healing.roll(), verbose)
            self.healing_spells -= 1

    def isalive(self):
        if self.hp>0: return 1

    def reset(self):
        self.hp=self.starting_hp
        self.healing_spells=self.starting_healing_spells

def battle(lineup, verbose=0,reset=0):
    if reset==1:
        for schmuck in lineup:
            schmuck.reset()
            #anything else?
    combattants=sorted(lineup, key=lambda fighter: fighter.initiative.roll())
    while True:
        for fighter in combattants:
            if fighter.isalive():
                #heal check -bonus action
                if fighter.starting_hp > (fighter.healing.dice+fighter.healing.bonus+fighter.hp):
                    fighter.cast_healing()
                #find targets
                targets=[opponent for opponent in combattants if (opponent.alignment != fighter.alignment) and (opponent.hp>0)]
                #find lowest target
                if len(targets)==0:
                    if verbose:
                        print("="*50)
                        for fighter in combattants:
                            print(fighter)
                    return fighter.alignment
                opponent=sorted(targets,key=lambda opponent: opponent.hp)[0]
                #attack it
                fighter.hit(opponent)


########### MAIN ######

import random

# fight(hero,baddie)
#hero = Creature("A","good",hp=10, healing_spells=0)
#heroine = Creature("B","good",hp=10, healing_spells=3)
#baddie = Creature("C","evil",hp=10)

bard = Creature("Bard","good",hp=18, healing_spells=6,healing_bonus=3, ac=18, initiative_bonus=2,attack_bonus=4, damage_bonus=2, damage_dice=8)
giant_toad=Creature("Giant Toad","evil",hp=39,ac=11,attack_bonus=4, damage_bonus=2, damage_dice=20)

from collections import Counter
rounds=1000
matchpoints=Counter([battle([bard, giant_toad],reset=1, verbose=0) for x in range(rounds)])
print({x: str(matchpoints[x]/rounds*100)+"%" for x in matchpoints.keys()})
