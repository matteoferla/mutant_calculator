__author__ = "Matteo"
__copyright__ = "Go away"
__email__ = "matteo.ferla@gmail.com"
__date__ = '25/03/15'

import random
import numpy as np
from collections import Counter

MUNCHKIN = 1

'''
Welcome to the D&D Battle simulator.

Go to the § HERE IS WHERE YOU CAN DECIDE THE LINE UP if you want to try it out.
The similator is set up as a munchkin combat where everyone targets the weakest due to find_weakest_target method of the Encounter class.
Changing MUNCHKIN (above) to 0 will use the find_random_target method —however, some muchkinishness still remains.
The muchkinishness has a deleterious side-effect when the method deathmatch of the Encounter class is invoked —this allocates each Creature object in the Encounter object in a different team.

The nitty-gritty:
There are three classes here: Dice, Character, Encounter.
Dice accepts bonus plus an int —8 is a d8— or a list of dice —[6,6] is a 2d6— or nothing —d20.
    roll() distinguishes between a d20 and not. d20 crits have to be passed manually.
Character has a boatload of attributes. Below in the main part there are a few monsters declared.
Encounter has the following attributes:
    battle(reset=1) does a single battle (after a reset of values if asked). it calls a few other fuctions such as roll_for_initiative()
    go_to_war(rounds=1000) performs many battles and gives the team results
    simulation… Complicated parameter tweaks to obtain plots
verbosity (verbose=1) is optional.

There are one or two approximations that are marked #NOT-RAW.
'''
######################DICE######################
class Dice:
    def __init__(self, bonus=0, dice=20):
        self.bonus = bonus
        if type(dice) is list:
            self.dice = dice
        else:
            self.dice = [dice]
        self.advantage = 0  # TBA
        self.crit = 0  # multiplier+1

    def multiroll(self, verbose=0):
        result = self.bonus
        for d in self.dice:
            for x in range(0, self.crit + 1): result += random.randint(1, d)
        self.crit = 0
        return result

    def icosaroll(self, verbose=0):
        self.crit = 0
        if self.advantage == 0:
            return self._crit_check(random.randint(1, 20), verbose) + self.bonus
        elif self.advantage == -1:  # AKA disadvatage
            return self._crit_check(sorted([random.randint(1, 20), random.randint(1, 20)])[0], verbose) + self.bonus
        elif self.advantage == 1:
            return self._crit_check(sorted([random.randint(1, 20), random.randint(1, 20)])[1], verbose) + self.bonus


    def _crit_check(self, result, verbose=0):
        if result == 1:
            if verbose: print("Fumble!")
            return -999  # automatic fail
        elif result == 20:
            if verbose: print("Crit!")
            self.crit = 1
            return 999  # automatic hit.
        else:
            return result

    def roll(self, verbose=0):  # THIS ASSUMES NO WEAPON DOES d20 DAMAGE!! Dragonstar and Siege engines don't.
        if self.dice[0] == 20:
            return self.icosaroll(verbose)
        else:
            return self.multiroll(verbose)


######################CREATURE######################

class Creature:
    def __init__(self, name, alignment="good", ac=10, initiative_bonus=0, hp=1, attack_parameters=[['club', 2, 0, 4]],
                 alt_attack=['none', 0],
                 healing_spells=0, healing_dice=4, healing_bonus=0, ability=[0, 0, 0, 0, 0, 0], sc_ability='wis',
                 buff='cast_nothing', buff_spells=0, log=None, xp=0):
        self.name = name
        self.ac = ac
        self.starting_hp = hp
        self.hp = hp
        self.initiative = Dice(initiative_bonus, 20)
        self.starting_healing_spells = healing_spells
        self.healing_spells = healing_spells
        self.healing = Dice(healing_bonus, healing_dice)
        self.attack_parameters = attack_parameters
        self.attacks = [
            {'name': monoattack[0], 'attack': Dice(monoattack[1], 20), 'damage': Dice(monoattack[2], monoattack[3:])}
            for monoattack in attack_parameters]
        self.alt_attack = {'name': alt_attack[0],
                           'attack': Dice(alt_attack[1], 20)}  # CURRENTLY ONLY NETTING IS OPTION!
        self.alignment = alignment
        self.ability = {y: Dice(x, 20) for x, y in zip(ability, ['str', 'dex', 'con', 'wis', 'int', 'cha'])}
        self.sc_ab = sc_ability
        # internal stuff
        self.tally_damage = 0
        self.tally_hits = 0
        self.tally_misses = 0
        self.tally_battles = 0
        self.tally_rounds = 0
        self.copy_index = 1
        self.condition = 'normal'
        self.dodge = 0
        self.concentrating = 0
        self.temp = 0
        self.buff_spells = buff_spells
        self.conc_fx = getattr(self, buff)
        self.log = log
        self.xp = xp

        self.hurtful = 0
        for x in self.attacks:
            self.hurtful += x['damage'].bonus
            self.hurtful += (sum(x['damage'].dice) + len(
                x['damage'].dice)) / 2  #the average roll of a d6 is not 3 but 3.5

    def copy(self):
        self.copy_index += 1
        return Creature(name=self.name + ' ' + str(self.copy_index), alignment=self.alignment, ac=self.ac,
                        initiative_bonus=self.initiative.bonus, hp=self.hp, attack_parameters=self.attack_parameters,
                        healing_spells=self.healing_spells, healing_dice=self.healing.dice[0],
                        healing_bonus=self.healing.bonus)


    def __str__(self):
        if self.tally_battles == 0: self.tally_battles = 1
        return self.name + ": {team=" + self.alignment + "; current hp=" + str(self.hp) + " (from " + str(
            self.starting_hp) + "); healing spells left=" + str(self.healing_spells) + " (from " + str(
            self.starting_healing_spells) + "); damage done (per battle average)= " + str(
            self.tally_damage / self.tally_battles) + "; hits/misses (PBA)= " + str(
            self.tally_hits / self.tally_battles) + "/" + str(
            self.tally_misses / self.tally_battles) + "; rounds (PBA)=" + str(
            self.tally_rounds / self.tally_battles) + ";}"

    def hit(self, opponent, i=0, verbose=0):
        adv = self.attacks[i]['attack'].advantage
        if opponent.dodge:
            self.attacks[i]['attack'].advantage = -1
        if opponent.condition == 'netted':
            self.attacks[i]['attack'].advantage = 1
        # Per coding it is impossible that a netted creature attempts an attack.
        if self.attacks[i]['attack'].roll(verbose) >= opponent.ac:
            self.attacks[i]['damage'].crit = self.attacks[i]['attack'].crit  #Pass the crit if present.
            h = self.attacks[i]['damage'].roll(verbose)
            opponent.wound(h, verbose)
            self.tally_damage += h
            self.tally_hits += 1
        else:
            self.tally_misses += 1
        self.attacks[i]['attack'].advantage = adv

    def net(self, opponent, verbose=0):
        adv = self.alt_attack['attack'].advantage
        if opponent.dodge:
            self.alt_attack['attack'].advantage = -1
        if opponent.condition == 'netted':
            print("ISSUE: ACTION WASTED NETTING A NETTED OPPONENT")
        if self.alt_attack['attack'].roll(verbose) >= opponent.ac:
            opponent.condition = 'netted'
            self.tally_hits += 1
            if verbose: print(self.name + " netted " + opponent.name)
        else:
            self.tally_misses += 1
        self.alt_attack['attack'].advantage = adv

    def wound(self, points, verbose=0):
        self.hp -= points
        if verbose: print(self.name + ' took ' + str(points) + ' of damage. Now on ' + str(self.hp) + ' hp.')
        if self.concentrating:
            dc = 5 + points
            if self.ability[self.sc_ab].roll() < dc:
                self.conc_fx()
                if verbose: print(self.name + ' has lost their concentration')

    def cast_barkskin(self):
        if self.concentrating == 0:
            self.temp = self.ac
            self.ac = 16
            self.concentrating = 1
        elif self.concentrating == 1:
            self.ac = self.temp
            self.concentrating = 0

    def cast_nothing(self, state='activate'):  # Something isn't quite right if this is invoked.
        pass

    def heal(self, points, verbose=0):
        self.hp += points
        if verbose: print(self.name + ' was healed by ' + str(points) + '. Now on ' + str(self.hp) + ' hp.')

    def cast_healing(self, weakling, verbose=0):
        if self.healing_spells > 0:
            weakling.heal(self.healing.roll(), verbose)
            self.healing_spells -= 1

    def isalive(self):
        if self.hp > 0: return 1

    def reset(self):
        self.hp = self.starting_hp
        if self.concentrating: self.conc_fx()
        self.healing_spells = self.starting_healing_spells


######################ARENA######################

class Encounter:
    def __init__(self, *lineup):
        # self.lineup={x.name:x for x in lineup}
        self.lineup = list(lineup)  #Classic fuck-up
        self.combattants = list(lineup)
        self.tally_rounds = 0
        self.tally_battles = 0
        self.name = 'Encounter'

    def add(self, newbie):
        self.combattants.append(newbie)

    def __str__(self):
        string = "=" * 50 + ' ' + self.name + " " + "=" * 50 + "\n"
        string += "Battles: " + str(self.tally_battles) + "; Sum of rounds:" + str(self.tally_rounds) + ";\n"
        for fighter in self.combattants: string += str(fighter) + "\n"
        return string

    def reset(self):
        for schmuck in self.combattants:
            schmuck.reset()

    def roll_for_initiative(self, verbose=0):
        self.combattants = sorted(self.lineup, key=lambda fighter: fighter.initiative.roll())
        if verbose:
            print("Turn order:")
            print([x.name for x in self.combattants])

    def battle(self, reset=1, verbose=0):
        self.tally_battles += 1
        if reset: self.reset()
        for schmuck in self.lineup:
            schmuck.tally_battles += 1
            # anything else?
        self.roll_for_initiative(verbose)
        while True:
            if verbose: print('**NEW ROUND**')
            self.tally_rounds += 1
            self.dodge = 0
            for character in self.combattants:
                if character.isalive():
                    character.tally_rounds += 1
                    if len(self.find_opponents(character)) == 0:
                        if verbose: print(self)
                        return character.alignment
                    # BONUS ACTION
                    # heal check -bonus action.
                    if character.healing_spells > 0:
                        weakling = self.find_wounded(character, verbose)
                        if weakling != 0:
                            character.cast_healing(weakling, verbose)
                    #Main action!
                    economy = len(self.find_allies(character)) > len(self.find_opponents(character)) > 0
                    #Buff?
                    if character.condition == 'netted':
                        #NOT-RAW: DC10 strength check or something equally easy for monsters
                        if verbose: print(character.name + " freed himself from a net")
                        character.condition = 'normal'
                    elif character.buff_spells > 0 and character.concentrating == 0:
                        character.conc_fx()
                        if verbose: print(character.name + ' buffs up!')
                        #greater action economy: waste opponent's turn.
                    elif economy and character is sorted(self.find_allies(character), key=lambda query: query.hp)[0]:
                        #weakest: dodge!
                        if verbose: print(character.name + " is dodging")
                        character.dodge = 1
                    elif economy and character.alt_attack['name'] == 'net':
                        opponent = self.find_target(character, verbose)
                        character.net(opponent, verbose)
                    else:
                        #MULTIATTACK!
                        for i in range(len(character.attacks)):
                            opponent = self.find_target(character, verbose)
                            if opponent == 0:  #has to be checked due to retargetting during multiattack.
                                if verbose: print(self)
                                return character.alignment
                            else:
                                character.hit(opponent, i, verbose)

    def find_target(self, searcher, verbose=0):
        if MUNCHKIN == 1:
            return self.find_weakest_target(searcher, verbose)
        else:
            return self.find_random_target(searcher, verbose)

    def find_weakest_target(self, searcher, verbose=0):
        targets = self.find_opponents(searcher)
        if len(targets) > 0:
            prey = sorted(targets, key=lambda query: query.hp)[0]
            if verbose: print(searcher.name + " targets " + prey.name + " (most squishy)")
            return prey
        else:
            return 0

    def find_random_target(self, searcher, verbose=0):
        targets = self.find_opponents(searcher)
        if len(targets) > 0:
            prey = random.choice(targets)
            if verbose: print(searcher.name + " targets " + prey.name + " (randomly)")
            return prey
        else:
            return 0

    def find_hurtful_target(self, searcher, verbose=0):
        targets = self.find_opponents(searcher)
        # targets=[enemy for enemy in self.find_opponents(searcher) if enemy.condition=='normal']
        if len(targets) > 0:
            bruisers = sorted(targets, key=lambda query: query.hurtful, reverse=True)
            prey = sorted(bruisers[0], key=lambda query: query.condition != 'normal')
            if verbose: print(searcher.name + " targets " + prey.name + " (biggest threat)")
            return prey
        else:
            return 0

    def find_opponents(self, searcher):
        return [query for query in self.combattants if (query.alignment != searcher.alignment) and (query.hp > 0)]

    def find_allies(self, searcher, verbose=0):
        return [query for query in self.combattants if (query.alignment == searcher.alignment)]

    def find_wounded(self, searcher, verbose=0):
        targets = self.find_allies(searcher)
        if len(targets) > 0:
            weakling = sorted(targets, key=lambda query: query.hp - query.starting_hp)[0]
            if weakling.starting_hp > (searcher.healing.dice[0] + searcher.healing.bonus + weakling.hp):
                if verbose: print(searcher.name + " wants to heal " + weakling.name)
                return weakling
            else:
                return 0
        else:
            raise NameError('A dead man wants to heal folk')

    def go_to_war(self, rounds=1000):
        return Counter([self.battle() for x in range(rounds)])

    # def simulate(self,tweak=None, rounds=1000):
    #
    #    Counter([self.battle() for x in range(rounds)])

    def deathmatch(self):
        colours = 'red blue green orange yellow lime cyan violet ultraviolet pink brown black white octarine teal magenta blue-green fuchsia purple cream grey'.split(
            ' ')
        for schmuck in self.combattants:
            schmuck.alignment = colours.pop(0) + " team"


########### MAIN #####


bard = Creature("Bard", "good",
                hp=18, ac=18,
                initiative_bonus=2,
                healing_spells=6, healing_bonus=3, healing_dice=4,
                attack_parameters=[['rapier', 4, 2, 8]], alt_attack=['net', 4, 0, 0])

doppelbard = Creature("Doppelbard", "good",
                      hp=18, ac=18,
                      healing_spells=6, healing_bonus=3,
                      initiative_bonus=2,
                      attack_parameters=[['rapier', 4, 2, 8]])

generic_tank = Creature("generic tank", "good",
                        hp=20, ac=18,
                        initiative_bonus=2,
                        attack_parameters=[['bastard sword', 5, 3, 10]])

mega_tank = Creature("mega tank", "good",
                     hp=24, ac=20,
                     initiative_bonus=2,
                     attack_parameters=[['great sword', 5, 3, 10]])

giant_toad = Creature("Giant Toad", "evil",
                      hp=39, ac=11,
                      attack_parameters=[['lick', 4, 2, 10, 10]])

barkskin_bear = Creature("Barkskinned Brown Bear", alignment="good",
                         hp=34, ac=16,
                         attack_parameters=[['claw', 5, 4, 8], ['bite', 5, 4, 6]])

barkskin_twibear = Creature("Druid twice as Barkskinned Brown Bear",
                            hp=86, ac=16, alignment="good",
                            attack_parameters=[['claw', 5, 4, 8], ['bite', 5, 4, 6]])

twibear = Creature("Twice Brown Bear Druid",
                   hp=86, ac=11, alignment="good",
                   attack_parameters=[['claw', 5, 4, 8], ['bite', 5, 4, 6]])

giant_rat = Creature("Giant Rat", "evil",
                     hp=7, ac=12,
                     initiative_bonus=2,
                     attack_parameters=[['bite', 4, 2, 3]])

commoner = Creature("Commoner", "good",
                    ac=10, hp=4,
                    attack_parameters=[['club', 2, 0, 4]])

goblin = Creature("Goblin", "evil",
                  ac=15, hp=7,
                  initiative_bonus=2,
                  attack_parameters=[['sword', 4, 2, 6]])

hill_giant = Creature("Hill Giant", "evil",
                      ac=13, hp=105,
                      attack_parameters=[['club', 8, 5, 8, 8, 8], ['club', 8, 5, 8, 8, 8]])

frost_giant = Creature("Frost Giant", "evil",
                       ac=15, hp=138,
                       attack_parameters=[['club', 9, 6, 12, 12, 12], ['club', 9, 6, 12, 12, 12]])

y_b_dragon = Creature("Young black dragon", "evil",
                      ac=18, hp=127,
                      initiative_bonus=2,
                      attack_parameters=[['1', 7, 4, 10, 10, 8], ['2', 7, 4, 6, 6], ['2', 7, 4, 6, 6]])

a_b_dragon = Creature("Adult black dragon (minus frightful)", "evil",
                      ac=19, hp=195, initiative_bonus=2,
                      attack_parameters=[['1', 11, 6, 10, 10], ['2', 11, 6, 6, 6], ['2', 11, 4, 6, 6]])

paradox = Creature("Paradox", "evil",
                   ac=10, hp=200,
                   attack_parameters=[['A', 2, 0, 1]])

druid = Creature("Twice Brown Bear Druid",
                 hp=86, ac=11, alignment="good",
                 attack_parameters=[['claw', 5, 4, 8], ['bite', 5, 4, 6, 6]], ability=[0, 0, 0, 0, 3, 0],
                 sc_ability='wis', buff='cast_barkskin', buff_spells=4,
                 log='The hp is bear x 2 + druid')

barbarian = Creature("Barbarian",
                     ac=18, hp=66, alignment="good",
                     attack_parameters=[['greatsword', 4, 1, 6, 6], ['frenzy greatsword', 4, 1, 6, 6]],
                     log="hp is doubled due to resistance")


##################################################################
################### HERE IS WHERE YOU CAN DECIDE THE LINE UP #####

rounds = 1000

# Skeezy vs. Gringo
if False:
    duel = Encounter(druid, barbarian)
    barbarian.alignment = "duelist"
    print(duel.go_to_war(10000))
    print(duel)

#CRx?
if True:
    arena = Encounter(druid, bard, generic_tank, barbarian, doppelbard,
                      a_b_dragon)
    #arena.battle(verbose=1)
    print(arena.go_to_war())
    print(arena)

if False:
    MUNCHKIN = 0  #Killing the weakest on PVP seems a bad strategy
    pvp = Encounter(druid, bard, generic_tank, barbarian, doppelbard)
    pvp.deathmatch()
    print(pvp.go_to_war())
    print(pvp)

#commoner vs. rat
if False:
    rounds=100
    report = np.zeros((10, 10))
    arena = Encounter(commoner, giant_rat)
    for y in range(1, 11):
        for x in range(1, 11):
            #Variants
            commoner.hp = 4 * x
            commoner.ac = 10 + y
            #battle…
            r = arena.go_to_war(rounds)
            report[x-1,y-1]=r['good']/rounds
    print(report)

### KILL PEACEFULLY
import sys

sys.exit(0)
#ANYTHING AFTER THIS WILL BE DISREGARDED

###DUMPYARD ###########
#CODE BELOW MAY BE BROKEN
