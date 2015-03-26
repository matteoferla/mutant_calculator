__author__ = "Matteo"
__copyright__ = "Go away"
__email__ = "matteo.ferla@gmail.com"
__date__ = '25/03/15'

class Dice:
    def __init__(self, bonus=0, dice=20, dice2=0,dice3=0,dice4=0):
        self.bonus = bonus
        self.dice = dice
        self.dice2 = dice2
        self.dice2 = dice3
        self.dice2 = dice4
        self.advantage=0 #TBA

    def roll(self):
        if self.dice2==0:
            return random.randint(1, self.dice) + self.bonus
        elif self.dice3==0:
            return random.randint(1, self.dice)+random.randint(1, self.dice2) + self.bonus
        elif self.dice4==0:
            return random.randint(1, self.dice)+random.randint(1, self.dice2)+random.randint(1, self.dice3) + self.bonus
        else:
            return random.randint(1, self.dice)+random.randint(1, self.dice2)+random.randint(1, self.dice3)+random.randint(1, self.dice4) + self.bonus



class Creature:
    def __init__(self, name, alignment="good", ac=10, initiative_bonus=0, hp=1, attack_bonus=0, damage_bonus=0, damage_dice=6,damage_dice2=0,damage_dice3=0,damage_dice4=0,
                 healing_spells=0, healing_dice=4, healing_bonus=0,multiattack=0, other_attack_bonus=0, other_damage_bonus=0, other_damage_dice=0,other_damage_dice2=0,other_damage_dice3=0,other_damage_dice4=0, further_attack_bonus=0, further_damage_bonus=0, further_damage_dice=0,further_damage_dice2=0,further_damage_dice3=0,further_damage_dice4=0):
        self.name = name
        self.ac = ac
        self.starting_hp = hp
        self.hp = hp
        self.initiative = Dice(initiative_bonus, 20)
        self.attack = Dice(attack_bonus, 20)
        self.damage = Dice(damage_bonus, damage_dice, damage_dice2,damage_dice3)
        self.starting_healing_spells = healing_spells
        self.healing_spells = healing_spells
        self.healing = Dice(healing_bonus,healing_dice)
        self.alignment=alignment
        self.multiattack=multiattack
        self.other_attack = Dice(other_attack_bonus, 20)
        self.other_damage = Dice(other_damage_bonus, other_damage_dice, other_damage_dice2, other_damage_dice3, other_damage_dice4)
        self.further_attack = Dice(further_attack_bonus, 20)
        self.further_damage = Dice(further_damage_bonus, further_damage_dice, further_damage_dice2, further_damage_dice3, further_damage_dice4)
        self.tally_damage=0
        self.tally_hits=0
        self.tally_misses=0


    def __str__(self):
        return self.name + ": {team="+self.alignment+"; current hp="+str(self.hp)+" (from "+str(self.starting_hp)+"); healing spells left="+str(self.healing_spells)+" (from "+str(self.starting_healing_spells)+"); damage done: "+str(self.tally_damage)+"; hits/misses: "+str(self.tally_hits)+"/"+str(self.tally_misses)+";}"

    def hit(self, opponent, verbose=0):
        if self.attack.roll() >= opponent.ac:
            h=self.damage.roll()
            opponent.wound(h,verbose)
            self.tally_damage +=h
            self.tally_hits +=1
        else:
            self.tally_misses +=1

    def other_hit(self, opponent, verbose=0):
        if self.other_attack.roll() >= opponent.ac:
            h=self.other_damage.roll()
            opponent.wound(h,verbose)
            self.tally_damage +=h
            self.tally_hits +=1
        else:
            self.tally_misses +=1

    def further_hit(self, opponent, verbose=0):
        if self.further_attack.roll() >= opponent.ac:
            h=self.further_damage.roll()
            opponent.wound(h,verbose)
            self.tally_damage +=h
            self.tally_hits +=1
        else:
            self.tally_misses +=1

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

    def aim(self,searchees, verbose=0):
        targets=[query for query in searchees if (query.alignment != self.alignment) and (query.hp>0)]
        if len(targets)>0:
            prey=sorted(targets,key=lambda query: query.hp)[0]
            if verbose: print(self.name+" targets "+prey.name)
            return prey
        else:
            return 0

def battle(lineup, verbose=0,reset=0):
    if reset==1:
        for schmuck in lineup:
            schmuck.reset()
            #anything else?
    combattants=sorted(lineup, key=lambda fighter: fighter.initiative.roll())
    while True:
        if verbose: print('**NEW ROUND**')
        for fighter in combattants:
            if fighter.isalive():
                #heal check -bonus action. Should heal all.
                if fighter.starting_hp > (fighter.healing.dice+fighter.healing.bonus+fighter.hp):
                    fighter.cast_healing()
                opponent=fighter.aim(combattants, verbose)
                if opponent==0:
                    if verbose: debrief(combattants)
                    return fighter.alignment
                else:
                    fighter.hit(opponent,verbose)
                if fighter.multiattack >0:
                    opponent=fighter.aim(combattants, verbose)
                    if opponent==0:
                        if verbose: debrief(combattants)
                        return fighter.alignment
                    else:
                        fighter.other_hit(opponent, verbose)
                if fighter.multiattack >1:
                    opponent=fighter.aim(combattants, verbose)
                    if opponent==0:
                        if verbose: debrief(combattants)
                        return fighter.alignment
                    else:
                        fighter.further_hit(opponent, verbose)


def debrief(combattants):
    print("="*50)
    for fighter in combattants: print(fighter)

########### MAIN ######

import random
from collections import Counter

#hero = Creature("A","good",hp=20, ac=18, healing_spells=0, attack_bonus=2)
#heroine = Creature("B","good",hp=14, healing_spells=3, attack_bonus=2)
#baddie = Creature("C","evil",hp=100)
bard = Creature("Bard","good",hp=18, healing_spells=6,healing_bonus=3, ac=18, initiative_bonus=2,attack_bonus=4, damage_bonus=2, damage_dice=8)
doppelbard= Creature("Doppelbard","good",hp=18, healing_spells=6,healing_bonus=3, ac=18, initiative_bonus=2,attack_bonus=4, damage_bonus=2, damage_dice=8)
generic_tank= Creature("generic tank","good",hp=20, healing_spells=0,healing_bonus=0, ac=18, initiative_bonus=2,attack_bonus=5, damage_bonus=3, damage_dice=10)
mega_tank= Creature("mega tank","good",hp=24, healing_spells=0,healing_bonus=0, ac=20, initiative_bonus=2,attack_bonus=5, damage_bonus=3, damage_dice=12)
giant_toad=Creature("Giant Toad","evil",hp=39,ac=11,attack_bonus=4, damage_bonus=2, damage_dice=10, damage_dice2=10)
barkskin_bear=Creature("Barkskinned Brown Bear", hp=34,ac=16,alignment="good", attack_bonus=5, damage_bonus=4, damage_dice=8,multiattack=1, other_attack_bonus=5, other_damage_bonus=4, other_damage_dice=6,other_damage_dice2=6)
barkskin_twibear=Creature("Druid twice as Barkskinned Brown Bear", hp=86,ac=16,alignment="good", attack_bonus=5, damage_bonus=4, damage_dice=8,multiattack=1, other_attack_bonus=5, other_damage_bonus=4, other_damage_dice=6,other_damage_dice2=6)
twibear=Creature("Twice Brown Bear Druid", hp=86,ac=11,alignment="good", attack_bonus=5, damage_bonus=4, damage_dice=8,multiattack=1, other_attack_bonus=5, other_damage_bonus=4, other_damage_dice=6,other_damage_dice2=6)
giant_rat=Creature("Giant Rat","evil",hp=7,ac=12,initiative_bonus=2,attack_bonus=4,damage_bonus=2, damage_dice=4)
commoner=Creature("Commoner","good",ac=10,hp=4,attack_bonus=2,damage_dice=4)
goblin=Creature("Goblin","evil",ac=15,hp=7,initiative_bonus=2,attack_bonus=4, damage_dice=6, damage_bonus=2)
hill_giant=Creature("Hill Giant","evil",ac=13,hp=105,attack_bonus=8,damage_bonus=5, damage_dice=8, damage_dice2=8, damage_dice3=8,multiattack=1, other_attack_bonus=8,other_damage_bonus=5, other_damage_dice=8, other_damage_dice2=8, other_damage_dice3=8)
frost_giant=Creature("Frost Giant","evil",ac=15,hp=138,attack_bonus=9,damage_bonus=6, damage_dice=12, damage_dice2=12, damage_dice3=12,multiattack=1, other_attack_bonus=9,other_damage_bonus=12, other_damage_dice=12, other_damage_dice2=12, other_damage_dice3=12)
y_b_dragon=Creature("Young black dragon","evil",ac=18,hp=127,initiative_bonus=2,attack_bonus=7, multiattack=2, damage_bonus=4, damage_dice=10, damage_dice2=10, damage_dice3=8,other_attack_bonus=7,other_damage_bonus=4, other_damage_dice2=6, other_damage_dice=6, further_attack_bonus=7, further_damage_bonus=4, further_damage_dice=6, further_damage_dice2=6)
a_b_dragon=Creature("Adult black dragon (minus frightful)","evil",ac=19,hp=195,initiative_bonus=2,attack_bonus=11, multiattack=2, damage_bonus=6, damage_dice=10, damage_dice2=10,other_attack_bonus=11,other_damage_bonus=6, other_damage_dice2=6, other_damage_dice=6, further_attack_bonus=11, further_damage_bonus=6, further_damage_dice=6, further_damage_dice2=6)


contestants=[a_b_dragon,barkskin_twibear,bard,generic_tank,mega_tank,doppelbard]

#battle(contestants,reset=1, verbose=1)

rounds=1000
matchpoints=Counter([battle(contestants,reset=1, verbose=0) for x in range(rounds)])
print(matchpoints)
debrief(sorted(contestants,key=lambda x: x.tally_damage))
