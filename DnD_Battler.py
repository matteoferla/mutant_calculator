__author__ = "Matteo"
__copyright__ = "Go away"
__email__ = "matteo.ferla@gmail.com"
__date__ = '25/03/15'


class Dice:
    def __init__(self, bonus=0, dice=20):
        self.bonus = bonus
        if type(dice) is list:
            self.dice = dice
        else:
            self.dice = [dice]
        self.advantage = 0  # TBA
        self.crit = 0  #multiplier+1

    def multiroll(self, verbose=0):
        result=self.bonus
        for d in self.dice:
            for x in range(0,self.crit+1): result += random.randint(1, d)
        self.crit=0
        return result

    def icosaroll(self, verbose=0):
        self.crit=0
        if self.advantage==0:
            result=random.randint(1, 20)
            if result==0:
                if verbose: print("Fumble!")
                return 0  #automatic fail
            elif result==20:
                if verbose: print("Crit!")
                self.crit=1
                return 999  #automatic hit
            result+=self.bonus
        return result

    def roll(self,verbose=0):    #THIS ASSUMES NO WEAPON DOES d20 DAMAGE!! Dragonstar and Siege engines don't.
        if self.dice[0]==20: return self.icosaroll(verbose)
        else: return self.multiroll(verbose)


class Creature:
    def __init__(self, name, alignment="good", ac=10, initiative_bonus=0, hp=1, attack_parameters=[['club',2,0,4]],
                 healing_spells=0, healing_dice=4, healing_bonus=0):
        self.name = name
        self.ac = ac
        self.starting_hp = hp
        self.hp = hp
        self.initiative = Dice(initiative_bonus, 20)
        self.starting_healing_spells = healing_spells
        self.healing_spells = healing_spells
        self.healing = Dice(healing_bonus, healing_dice)
        self.alignment = alignment
        self.tally_damage = 0
        self.tally_hits = 0
        self.tally_misses = 0
        self.tally_battles = 0
        self.tally_rounds = 0
        self.copy_index=1
        self.attack_parameters=attack_parameters
        self.attacks=[{'name':monoattack[0],'attack':Dice(monoattack[1], 20),'damage':Dice(monoattack[2], monoattack[3:])} for monoattack in attack_parameters]

    def copy(self):
        self.copy_index +=1
        return Creature(name=self.name+' '+str(self.copy_index), alignment=self.alignment, ac=self.ac, initiative_bonus=self.initiative.bonus, hp=self.hp, attack_parameters=self.attack_parameters,
                 healing_spells=self.healing_spells, healing_dice=self.healing.dice[0], healing_bonus=self.healing.bonus)


    def __str__(self):
        if self.tally_battles==0: self.tally_battles =1
        return self.name + ": {team=" + self.alignment + "; current hp=" + str(self.hp) + " (from " + str(
            self.starting_hp) + "); healing spells left=" + str(self.healing_spells) + " (from " + str(
            self.starting_healing_spells) + "); damage done (per battle average)= " + str(self.tally_damage/self.tally_battles) + "; hits/misses (PBA)= " + str(
            self.tally_hits/self.tally_battles) + "/" + str(self.tally_misses/self.tally_battles) + "; rounds (PBA)="+str(self.tally_rounds/self.tally_battles)+";}"

    def hit(self, opponent, i=0, verbose=0):
        if self.attacks[i]['attack'].roll(verbose) >= opponent.ac:
            self.attacks[i]['damage'].crit=self.attacks[i]['attack'].crit #Pass the crit if present.
            h = self.attacks[i]['damage'].roll(verbose)
            opponent.wound(h, verbose)
            self.tally_damage += h
            self.tally_hits += 1
        else:
            self.tally_misses += 1

    def wound(self, points, verbose=0):
        self.hp -= points
        if verbose: print(self.name + ' took ' + str(points) + ' of damage. Now on ' + str(self.hp) + ' hp.')

    def heal(self, points, verbose=0):
        self.hp += points
        if verbose: print(self.name + ' was healed by ' + str(points) + '. Now on ' + str(self.hp) + ' hp.')

    def cast_healing(self, weakling,verbose=0):
        if self.healing_spells > 0:
            weakling.heal(self.healing.roll(), verbose)
            self.healing_spells -= 1

    def isalive(self):
        if self.hp > 0: return 1

    def reset(self):
        self.hp = self.starting_hp
        self.healing_spells = self.starting_healing_spells

    def aim(self, searchees, verbose=0):
        targets = [query for query in searchees if (query.alignment != self.alignment) and (query.hp > 0)]
        if len(targets) > 0:
            prey = sorted(targets, key=lambda query: query.hp)[0]
            if verbose: print(self.name + " targets " + prey.name)
            return prey
        else:
            return 0

    def search_for_wounded(self, searchees, verbose=0):
        targets = [query for query in searchees if (query.alignment == self.alignment)]
        if len(targets) > 0:
            weakling = sorted(targets, key=lambda query: query.hp-query.starting_hp)[0]
            if weakling.starting_hp > (self.healing.dice[0] + self.healing.bonus + weakling.hp):
                if verbose: print(self.name + " wants to heal " + weakling.name)
                return weakling
            else:
                return 0
        else:
            raise NameError('A dead man wants to heal folk')


def battle(lineup, verbose=0, reset=0):
    if reset == 1:
        for schmuck in lineup:
            schmuck.reset()
            schmuck.tally_battles += 1
            # anything else?
    combattants = sorted(lineup, key=lambda fighter: fighter.initiative.roll())
    while True:
        if verbose: print('**NEW ROUND**')
        for character in combattants:
            if character.isalive():
                character.tally_rounds +=1
                # heal check -bonus action. Req: Should heal all.
                if character.healing_spells>0:
                    weakling=character.search_for_wounded(combattants,verbose)
                    if weakling !=0:
                        character.cast_healing(weakling,verbose)
                #attack!
                for i in range(len(character.attacks)):
                    opponent = character.aim(combattants, verbose)
                    if opponent == 0:
                        if verbose: debrief(combattants)
                        return character.alignment
                    else:
                        character.hit(opponent, i, verbose)

def debrief(combattants):
    print("=" * 50)
    for fighter in combattants: print(fighter)

########### MAIN ######

import random
from collections import Counter


bard = Creature("Bard", "good",
                hp=18, ac=18,
                initiative_bonus=2,
                healing_spells=6, healing_bonus=3, healing_dice=4,
                attack_parameters=[['rapier',4,2,8]])

doppelbard = Creature("Doppelbard", "good",
                      hp=18, ac=18,
                      healing_spells=6, healing_bonus=3,
                      initiative_bonus=2,
                      attack_parameters=[['rapier',4,2,8]])

generic_tank = Creature("generic tank", "good",
                        hp=20, ac=18,
                        initiative_bonus=2,
                        attack_parameters=[['bastard sword',5,3,10]])

mega_tank = Creature("mega tank", "good",
                     hp=24, ac=20,
                     initiative_bonus=2,
                     attack_parameters=[['great sword',5,3,10]])

giant_toad = Creature("Giant Toad", "evil",
                      hp=39, ac=11,
                      attack_parameters=[['lick',4,2,10,10]])

barkskin_bear = Creature("Barkskinned Brown Bear", alignment="good",
                         hp=34, ac=16,
                         attack_parameters=[['claw',5,4,8],['bite',5,4,6]])

barkskin_twibear = Creature("Druid twice as Barkskinned Brown Bear",
                            hp=86, ac=16, alignment="good",
                            attack_parameters=[['claw',5,4,8],['bite',5,4,6]])

twibear = Creature("Twice Brown Bear Druid",
                   hp=86, ac=11, alignment="good",
                   attack_parameters=[['claw',5,4,8],['bite',5,4,6]])

giant_rat = Creature("Giant Rat", "evil",
                     hp=7, ac=12,
                     initiative_bonus=2,
                     attack_parameters=[['bite',4,2,3]])

commoner = Creature("Commoner", "good",
                    ac=10, hp=4,
                    attack_parameters=[['club',2,0,4]])

goblin = Creature("Goblin", "evil",
                  ac=15, hp=7,
                  initiative_bonus=2,
                  attack_parameters=[['sword',4,2,6]])

hill_giant = Creature("Hill Giant", "evil",
                      ac=13, hp=105,
                      attack_parameters=[['club',8,5,8,8,8],['club',8,5,8,8,8]])

frost_giant = Creature("Frost Giant", "evil",
                       ac=15, hp=138,
                       attack_parameters=[['club',9,6,12,12,12],['club',9,6,12,12,12]])

y_b_dragon = Creature("Young black dragon", "evil",
                      ac=18, hp=127,
                      initiative_bonus=2,
                      attack_parameters=[['1',7,4,10,10,8],['2',7,4,6,6],['2',7,4,6,6]])

a_b_dragon = Creature("Adult black dragon (minus frightful)", "evil",
                      ac=19, hp=195, initiative_bonus=2,
                      attack_parameters=[['1',11,6,10,10],['2',11,6,6,6],['2',11,4,6,6]])

paradox=Creature("Paradox", "evil",
                    ac=10, hp=200,
                    attack_parameters=[['A',2,0,1]])

##################################################################

rounds = 1000

#contestants=[hill_giant,bard,commoner]
contestants = [y_b_dragon, barkskin_twibear, bard, generic_tank, mega_tank, doppelbard]

#mega_tank.wound(10,1)
#contestants = [giant_rat, giant_rat.copy(),giant_rat.copy(), giant_rat.copy(),giant_rat.copy(),giant_rat.copy(),bard, mega_tank, doppelbard]
#contestants=[paradox,barkskin_twibear]

matchpoints = Counter([battle(contestants, reset=1, verbose=0) for x in range(rounds)])
print(matchpoints)

### KILL PEACEFULLY
import sys
sys.exit(0)

###DUMPYARD ###########


matchpoints = Counter([battle(contestants, reset=1, verbose=0) for x in range(rounds)])
print(matchpoints)
#debrief(sorted(contestants, key=lambda x: x.tally_damage))


#rats=[Creature("Giant Rat","evil",hp=7,ac=12,initiative_bonus=2,attack_bonus=4,damage_bonus=2, damage_dice=4) for x in range(5)]
#matchpoints=Counter([battle([hill_giant],reset=1, verbose=0) for x in range(rounds)])

for y in range(1,1000):
    mob=[Creature("Commoner","good",ac=10,hp=4,attack_bonus=2,damage_dice=4) for x in range(y)]
    matchpoints=Counter([battle([hill_giant]+mob,reset=1, verbose=0) for x in range(rounds)])
    print(str(y)+"..."+str({x: str(matchpoints[x]/rounds*100)+"%" for x in sorted(matchpoints.keys())}))


for z in range(1,10):
    print(z)
    for y in range(1,20):
        mod_commoner=Creature("Commoner","good",ac=10,hp=4*z,attack_bonus=2,damage_dice=y,damage_dice2=y)
        matchpoints=Counter([battle([mod_commoner,giant_rat],reset=1, verbose=0) for x in range(rounds)])
        #print({x: str(matchpoints[x]/rounds*100)+"%" for x in sorted(matchpoints.keys())})
        print(matchpoints["good"]/rounds*100)


#rats=[Creature("Giant Rat","evil",hp=7,ac=12,initiative_bonus=2,attack_bonus=4,damage_bonus=2, damage_dice=4) for x in range(5)]
#battle([barkskin_bear]+rats,reset=1, verbose=1)

for y in range(20):
    rounds=10000
    rats=[Creature("Giant Rat","evil",hp=7,ac=12,initiative_bonus=2,attack_bonus=4,damage_bonus=2, damage_dice=4) for x in range(y)]
    matchpoints=Counter([battle([barkskin_twibear]+rats,reset=1, verbose=0) for x in range(rounds)])
    print(matchpoints["good"]/rounds*100)
    #print({x: str(matchpoints[x]/rounds*100)+"%" for x in sorted(matchpoints.keys())})
