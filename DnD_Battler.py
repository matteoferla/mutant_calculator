__author__ = "Matteo"
__copyright__ = "Don't blame me for a TPK"
__email__ = "matteo.ferla@gmail.com"
__date__ = '25/03/15'

import random
import math
from collections import Counter

TARGET ='enemy alive weakest'
#target='enemy alive weakest', target='enemy alive random', target='enemy alive fiersomest'

'''
Welcome to the D&D Battle simulator.

Go to the § HERE IS WHERE YOU CAN DECIDE THE LINE UP if you want to try it out.
The similator is set up as a munchkin combat where everyone targets the weakest due to find_weakest_target method of the Encounter class.
Changing TARGET (above) to something else will change the targetting.
The muchkinishness has a deleterious side-effect when the method deathmatch of the Encounter class is invoked —this allocates each Creature object in the Encounter object in a different team.

The nitty-gritty:
There are three classes here: Dice, Character, Encounter.
Dice accepts bonus plus an int —8 is a d8— or a list of dice —[6,6] is a 2d6— or nothing —d20.
    roll() distinguishes between a d20 and not. d20 crits have to be passed manually.
Character has a boatload of attributes. Below in the main part there are a few monsters declared.
Encounter includes the following method:
    battle(reset=1) does a single battle (after a reset of values if asked). it calls a few other fuctions such as roll_for_initiative()
    go_to_war(rounds=1000) performs many battles and gives the team results
verbosity (verbose=1) is optional.

There is some code messiness resulting from the unclear distinction between Encounter and Creature object, namely
a Creature interacting with another is generally a Creature method, while a Creature searching across the list of Creatures in the Encounter is an Encounter method.

There are one or two approximations that are marked #NOT-RAW. In the Encounter.battle method there are some thought on the action choices.
'''
######################DICE######################
class Dice:
    def __init__(self, bonus=0, dice=20, avg = False):
        self.bonus = bonus
        if type(dice) is list:
            self.dice = dice
        else:
            self.dice = [dice]
        self.advantage = 0  # TBA
        self.crit = 0  # multiplier+1. Actually you can't get a crit train anymore.
        self.avg = avg

    def __str__(self):
        s=''
        if len(self.dice)==1: s +='d'+str(self.dice[0])+'+'
        elif len(self.dice)==2 and self.dice[0] == self.dice[1]: s +='2d'+str(self.dice[0])+'+'
        elif len(self.dice)==2 and self.dice[0]!= self.dice[1]: s +='d'+str(self.dice[0])+'+d'+'d'+str(self.dice[1])+'+'
        elif len(self.dice)==3 and self.dice[0] == self.dice[1] == self.dice[1]: s +='3d'+str(self.dice[0])+'+'
        elif len(self.dice)==3 and self.dice[0]!= self.dice[1]: s +='d'+str(self.dice[0])+'+d'+str(self.dice[1])+'+d'+str(self.dice[1])+'+'
        else:
            for x in range(len(self.dice)):
                s+='d'+str(self.dice[x])+'+'
        s +=str(self.bonus)
        return s


    def multiroll(self, verbose=0):
        result = self.bonus
        for d in self.dice:
            if self.avg:  #NPC rolls
                if self.crit:
                    result += d
                else:
                    result +=round(d/2+1)
            else:
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

    def roll(self, crit=None, verbose=0):  # THIS ASSUMES NO WEAPON DOES d20 DAMAGE!! Dragonstar and Siege engines don't.
        if self.dice[0] == 20:
            return self.icosaroll(verbose)
        else:
            if crit:
                self.crit=crit
            return self.multiroll(verbose)


######################CREATURE######################

class Creature:
    def __init__(self, name, alignment="good", ac=10, initiative_bonus=None, hp=None, attack_parameters=[['club', 2, 0, 4]],
                 alt_attack=['none', 0],
                 healing_spells=0, healing_dice=4, healing_bonus=None, ability=[0, 0, 0, 0, 0, 0], sc_ability='wis',
                 buff='cast_nothing', buff_spells=0, log=None, xp=0, hd=6, level=1, proficiency=2):

        self.name = name
        self.ac = ac

        #build from scratch
        self.proficiency=proficiency
        if isinstance(ability, list):
            self.ability = {y: x for x, y in zip(ability, ['str', 'dex', 'con', 'wis', 'int', 'cha'])}
        elif isinstance(ability, dict):
            self.ability = {'str':0, 'dex':0, 'con':0, 'wis':0, 'int':0, 'cha':0}
            self.ability.update(ability)
        else:
            raise NameError('ability can be a list of six, or a incomplete dictionary')
        self.hd=Dice(self.ability['con'],hd, avg=True)
        if hp:
            self.hp = hp
            self.starting_hp = self.hp
        else:
            self.set_level(level)
        #init
        if not initiative_bonus:
            initiative_bonus=self.ability['dex']
        self.initiative = Dice(initiative_bonus, 20)
        #spell
        self.sc_ab = sc_ability  #spell casting ability
        if not healing_bonus:
            healing_bonus=self.ability[self.sc_ab]
        self.starting_healing_spells = healing_spells
        self.healing_spells = healing_spells
        self.healing = Dice(healing_bonus, healing_dice)
        self.attacks=[]
        self.hurtful = 0
        self.attack_parameters = attack_parameters
        self.attack_parse(attack_parameters)
        self.alt_attack = {'name': alt_attack[0],
                           'attack': Dice(alt_attack[1], 20)}  # CURRENTLY ONLY NETTING IS OPTION!
        self.alignment = alignment
        # internal stuff
        self.tally={'damage':0, 'hits':0, 'misses':0, 'battles':0, 'rounds':0, 'hp': self.hp, 'healing_spells':self.healing_spells}
        self.copy_index = 1
        self.condition = 'normal'

        self.dodge = 0
        self.concentrating = 0
        self.temp = 0
        self.buff_spells = buff_spells
        self.conc_fx = getattr(self, buff)
        self.log = log
        self.xp = xp
        self.arena=None

    def set_level(self, level):
        self.hp=0
        self.hd.crit=1  #Not-RAW first level is always max for PCs, but not monsters.
        for x in range(level):
            self.hp +=self.hd.roll()
        self.level=level
        self.starting_hp=self.hp
        self.proficiency=1+round((level)/4)
        #self.attack_parse(attack_parameters)

    def copy(self):
        self.copy_index += 1
        return Creature(name=self.name + ' ' + str(self.copy_index), alignment=self.alignment, ac=self.ac,
                        initiative_bonus=self.initiative.bonus, hp=self.hp, attack_parameters=self.attack_parameters,
                        healing_spells=self.healing_spells, healing_dice=self.healing.dice[0],
                        healing_bonus=self.healing.bonus)

    def attack_parse(self,attack_parameters):
        self.attacks = [
            {'name': monoattack[0], 'attack': Dice(monoattack[1], 20), 'damage': Dice(monoattack[2], monoattack[3:])}
            for monoattack in attack_parameters]
        for x in self.attacks:
            self.hurtful += x['damage'].bonus
            self.hurtful += (sum(x['damage'].dice) + len(
                x['damage'].dice)) / 2  #the average roll of a d6 is not 3 but 3.5


    def __str__(self):
        battles=1
        if self.tally['battles'] > 0:
            battles=self.tally['battles']
            #I should fix it up afterwards
        return self.name + ": {team=" + self.alignment + "; current hp=" + str(self.tally['hp'] / battles) + " (from " + str(
            self.starting_hp) + "); healing spells left=" + str(self.tally['healing_spells'] / battles) + " (from " + str(
            self.starting_healing_spells) + "); damage done (per battle average)= " + str(
            self.tally['damage'] / battles) + "; hits/misses (PBA)= " + str(
            self.tally['hits'] / battles) + "/" + str(
            self.tally['misses'] / battles) + "; rounds (PBA)=" + str(
            self.tally['rounds'] / battles) + ";}"

    def isalive(self):
        if self.hp > 0: return 1

    def take_damage(self, points, verbose=0):
        self.hp -= points
        if verbose: print(self.name + ' took ' + str(points) + ' of damage. Now on ' + str(self.hp) + ' hp.')
        if self.concentrating:
            dc = points/2
            if dc <10: dc=10
            if Dice(self.ability[self.sc_ab]).roll() < dc:
                self.conc_fx()
                if verbose: print(self.name + ' has lost their concentration')

    def ready(self):
        self.dodge=0
        #there should be a few more.
        #conditions.

    def reset(self):
        self.hp = self.starting_hp
        if self.concentrating: self.conc_fx()
        self.healing_spells = self.starting_healing_spells

    def check_advantage(self,opponent):
        adv=0
        if opponent.dodge:
            adv += -1
        if (opponent.condition == 'netted') or (opponent.condition == 'restrained'):
            adv += 1
        # Per coding it is impossible that a netted creature attempts an attack.
        if (self.condition == 'netted') or (self.condition == 'restrained'):
            adv += -1
        return adv

    def net(self, opponent, verbose=0):
        self.alt_attack['attack'].advantage= self.check_advantage(opponent)
        if self.alt_attack['attack'].roll(verbose) >= opponent.ac:
            opponent.condition = 'netted'
            self.tally['hits'] += 1
            if verbose: print(self.name + " netted " + opponent.name)
        else:
            self.tally['misses'] += 1


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


    def assess_wounded(self, verbose=0):
            targets = self.arena.find('bloodiest allies',team=self.alignment)
            if len(targets) > 0:
                weakling = targets[0]
                if weakling.starting_hp > (self.healing.dice[0] + self.healing.bonus + weakling.hp):
                    if verbose: print(self.name + " wants to heal " + weakling.name)
                    return weakling
                else:
                    return 0
            else:
                raise NameError('A dead man wants to heal folk')

    def cast_healing(self, weakling, verbose=0):
        if self.healing_spells > 0:
            weakling.heal(self.healing.roll(), verbose)
            self.healing_spells -= 1

    def multiattack(self,verbose=0, assess=0):
        if assess:
            return 0  #the default
        for i in range(len(self.attacks)):
            try:
                opponent = self.arena.find(TARGET,self, verbose)[0]
            except IndexError:
                raise self.arena.Victory()
            if verbose:
                print(self.name + ' attacks '+opponent.name+' with '+self.attacks[i]['name'])
            #This was the hit method. put here for now.
            self.attacks[i]['attack'].advantage = self.check_advantage(opponent)
            if self.attacks[i]['attack'].roll(verbose) >= opponent.ac:
                self.attacks[i]['damage'].crit = self.attacks[i]['attack'].crit  #Pass the crit if present.
                h = self.attacks[i]['damage'].roll(verbose)
                opponent.take_damage(h, verbose)
                self.tally['damage'] += h
                self.tally['hits'] += 1
            else:
                self.tally['misses'] += 1

    #TODO
    def check_action(self,action, verbose):
        return getattr(self, action)(assess=1)

    #TODO
    def do_action(self,action, verbose):
        #do it.
        pass

    #TODO
    def TBA_act(self,verbose=0):
        if not self.arena.find('alive enemy'):
            raise Encounter.Victory()
        x={'nothing':'cast_nothing'}
        choice=[self.check_action(x) for x in self.actions]
        best=sorted(choice.keys(),key=choice.get)[0]
        self.do_action(best)

    def act(self,verbose=0):
        if not self.arena.find('alive enemy'):
            raise Encounter.Victory()
        # BONUS ACTION
        # heal  -healing word, a bonus action.
        if self.healing_spells > 0:
            weakling = self.assess_wounded(verbose)
            if weakling != 0:
                self.cast_healing(weakling, verbose)
        #Main action!
        economy = len(self.arena.find('allies')) > len(self.arena.find('opponents')) > 0
        #Buff?
        if self.condition == 'netted':
            #NOT-RAW: DC10 strength check or something equally easy for monsters
            if verbose: print(self.name + " freed himself from a net")
            self.condition = 'normal'
        elif self.buff_spells > 0 and self.concentrating == 0:
            self.conc_fx()
            if verbose: print(self.name + ' buffs up!')
            #greater action economy: waste opponent's turn.
        elif economy and self is self.arena.find('weakest allies')[0]:
            if verbose: print(self.name + " is dodging")
            self.dodge = 1
        elif economy and self.alt_attack['name'] == 'net':
            opponent = self.arena.find('fiersomest enemy alive', self, verbose)[0]
            if opponent.condition !='netted':
                self.net(opponent, verbose)
            else:
                self.multiattack(verbose)
        else:
            self.multiattack(verbose)



######################ARENA######################
class Encounter():
    class Victory(Exception):
        pass

    def __init__(self, *lineup):
        # self.lineup={x.name:x for x in lineup}
        #self.lineup = list(lineup)  #Classic fuck-up
        self.combattants = list(lineup)
        for chap in lineup:
            chap.arena=self
        self.tally={'rounds':0, 'battles': 0, 'perfect': None, 'close':None, 'victories':None}
        self.active=lineup[0]
        self.name = 'Encounter'
        self.check()
        self.note=''

    def check(self):
        #TODO Should keep originals if present
        self.sides = set([dude.alignment for dude in self])
        self.tally['perfect'] = {side: 0 for side in self.sides}
        self.tally['close'] = {side: 0 for side in self.sides}
        self.tally['victories'] = {side: 0 for side in self.sides}

    def append(self, newbie):
        self.combattants.append(newbie)
        newbie.arena=self
        self.check()

    def extend(self, iterable):
        for x in iterable:
            self.append(x)

    def __str__(self):
        string = "=" * 50 + ' ' + self.name + " " + "=" * 50 + "\n"
        string += self.predict()
        string += "-"*110+"\n"
        string += "Battles: " + str(self.tally['battles']) + "; Sum of rounds: " + str(self.tally['rounds']) + "; " + self.note + "\n"
        for s in self.sides:
            string += "> Team " + str(s) + " = winning battles: " + str(self.tally['victories'][s]) + "; perfect battles: " + str(self.tally['perfect'][s]) + "; close-call battles: " + str(self.tally['close'][s])+ ";\n"
        string += "-" * 49 + " Combattants  " + "-" * 48 + "\n"
        for fighter in self.combattants: string += str(fighter) + "\n"
        return string

    def __len__(self):
        return len(self.combattants)

    def __add__(self, other):
        self.extend(other)

    def __iter__(self):
        return iter(self.combattants)

    def __getitem__(self, item):
        for character in self:
            if character.name == item:
                return character
        raise Exception('Nobody by this name')

    def reset(self):
        for schmuck in self.combattants:
            schmuck.reset()
        return self

    def set_deathmatch(self):
        colours = 'red blue green orange yellow lime cyan violet ultraviolet pink brown black white octarine teal magenta blue-green fuchsia purple cream grey'.split(
            ' ')
        for schmuck in self:
            schmuck.alignment = colours.pop(0) + " team"
        return self

    def roll_for_initiative(self, verbose=0):
        self.combattants = sorted(self.combattants, key=lambda fighter: fighter.initiative.roll())
        if verbose:
            print("Turn order:")
            print([x.name for x in self])

    __doc__ = '''
    Battle…
    In a dimentionless model, move action and the main actions dash, disengage, hide, shove back/aside, tumble and overrun are meaningless.
    weapon attack —default
    two-weapon attack —
        Good when the opponent has low AC (<12) if 2nd attack is without proficiency.
        Stacks with bonuses such as sneak attack or poisoned weapons —neither are in the model.
        Due to the 1 action for donning/doffing a shield, switch to two handed is valid for unshielded folk only.
        Best keep two weapon fighting as a prebuild not a combat switch.
    AoE spell attack — Layout…
    targetted spell attack —produce flame is a cantrip so could be written up as a weapon. The bigger ones. Spell slots need to be re-written.
    spell buff —Barkskin is a druidic imperative. Haste? Too much complication.
    spell debuff —Bane…
    dodge —targetted and turn economy
    help —high AC target (>18), turn economy, beefcake ally
    ready —teamwork preplanning. No way.
    grapple/climb —very situational. grapple/shove combo or barring somatic.
    disarm —disarm… grey rules about whether picking it up or kicking it away is an interact/move/bonus/main action.
        netting is a better option albeit a build.
    called shot —not an official rule. Turn economy.
    '''
    def predict(self):
        def not_us(side):
            (a,b)=list(self.sides)
            if a == side:
                return b
            else:
                return a
        if len(self.sides) !=2:
            #print('Calculations unavailable for more than 2 teams')
            return ""
        t_ac={x:[] for x in self.sides}
        for character in self:
            t_ac[character.alignment].append(character.ac)
        ac={x: sum(t_ac[x])/len(t_ac[x]) for x in t_ac.keys()}
        damage={x:0 for x in self.sides}
        hp={x:0 for x in self.sides}
        for character in self:
            for move in character.attacks:
                move['damage'].avg=True
                damage[character.alignment]+= (20+move['attack'].bonus-ac[not_us(character.alignment)])/20*move['damage'].roll()
                move['damage'].avg=False
                hp[character.alignment]+= character.starting_hp
        (a,b)=list(self.sides)
        rate={a: hp[a]/damage[b], b: hp[b]/damage[a]}
        return ('Rough a priori predictions: «WARNING: EXPERIMENTAL SECTION»'+"\n"+
                '> '+ a + '= expected rounds to survive: ' + str(round(rate[a],2))+'; badly normalised: ' + str(round(rate[a]/(rate[a]+rate[b])*100))+ '%'+"\n"+
                '> '+ b + '= expected rounds to survive: ' + str(round(rate[b],2))+'; badly normalised: ' + str(round(rate[b]/(rate[a]+rate[b])*100))+ '%'+"\n")

    def battle(self,reset=1,verbose=1):
        self.tally['battles'] += 1
        if reset: self.reset()
        for schmuck in self: schmuck.tally['battles'] += 1
        self.roll_for_initiative(verbose)
        while True:
            try:
                if verbose: print('**NEW ROUND**')
                self.tally['rounds'] += 1
                for character in self:
                    character.ready()
                    if character.isalive():
                        self.active=character
                        character.tally['rounds'] += 1
                        character.act(verbose)
            except Encounter.Victory:
                break
        #closing up maths
        side=self.active.alignment
        team=self.find('allies')
        self.tally['victories'][side] += 1
        perfect=1
        close=0
        for x in team:
            if x.hp < x.starting_hp:
                perfect = 0
            if x.hp < 0:
                close =1
        if not perfect:
            self.tally['perfect'][side] += perfect
        self.tally['close'][side] += close
        for character in self:
            character.tally['hp'] +=character.hp
            character.tally['healing_spells'] +=character.healing_spells
        if verbose: print(self)
        #return self or side?
        return self

    def go_to_war(self, rounds=1000):
        for i in range(rounds):
            self.battle(1,0)
        x={y:self.tally['victories'][y] for y in self.sides}
        se={}
        for i in list(x):
            x[i] /= rounds
            try:
                se[i]=math.sqrt(x[i]*(1-x[i])/rounds)
            except Exception:
                se[i]="NA"
        self.reset()
        for i in list(x):
            self.note +=str(i) +': ' + str(round(x[i],2)) +' ± ' + str(round(se[i],2)) + '; '
        return self


    def find(self, what, searcher=None, team=None):

        def _enemies(folk):
            return [query for query in folk if (query.alignment != team)]

        def _allies(folk):
            return [query for query in folk if (query.alignment == team)]

        def _alive(folk):
            return [query for query in folk if (query.hp > 0)]

        def _normal(folk):
            return [joe for joe in folk if joe.condition == 'normal']

        def _random(folk):
            return random.shuffle(folk)

        def _weakest(folk):
            return sorted(folk, key=lambda query: query.hp)

        def _bloodiest(folk):
            return sorted(folk, key=lambda query: query.hp - query.starting_hp)

        def _fiersomest(folk):
            return sorted(folk, key=lambda query: query.hurtful, reverse=True)

        def _opponents(folk):
            return _alive(_enemies(folk))

        searcher = searcher or self.active
        team = team or searcher.alignment
        folk=self.combattants
        agenda=list(what.split(' '))
        opt={
            'enemies':_enemies,
            'enemy':_enemies,
            'opponents':_opponents,
            'allies':_allies,
            'ally':_allies,
            'normal':_normal,
            'alive':_alive,
            'fiersomest':_fiersomest,
            'weakest':_weakest,
            'random':_random,
            'bloodiest':_bloodiest
        }
        for cmd in list(agenda):
            if folk==None:
                folk=[]
            for o in opt:
                if (cmd == o):
                    folk= opt[o](folk)
                    agenda.remove(cmd)
        if agenda:
            raise Exception(str(cmd) + ' field not found')
        return folk

########### MAIN #####



netsharpshooter = Creature("net-build bard", "good",
                hp=18, ac=18,
                initiative_bonus=2,
                healing_spells=6, healing_bonus=3, healing_dice=4,
                attack_parameters=[['rapier', 4, 2, 8]], alt_attack=['net', 4, 0, 0], level=3)
Creature("Bard", "good",
                      hp=18, ac=18,
                      healing_spells=6, healing_bonus=3, healing_dice=4,
                      initiative_bonus=2,
                      attack_parameters=[['rapier', 4, 2, 8]])

generic_tank = Creature("generic tank", "good",
                        hp=20, ac=17,
                        initiative_bonus=2,
                        attack_parameters=[['great sword', 5, 3, 6,6]])

mega_tank = Creature("mega tank", "good",
                     hp=24, ac=17,
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
                     attack_parameters=[['bite', 4, 2, 4]])

commoner = Creature("Commoner", "good",
                    ac=10, hp=4,
                    attack_parameters=[['club', 2, 0, 4]])

bob = Creature("Bob", "mad",
                    ac=10, hp=8,
                    attack_parameters=[['club', 2, 0, 4],['club', 2, 0, 4]])

joe = Creature("Joe", "good",
                    ac=17, hp=103, #bog standard leather-clad level 3.
                    attack_parameters=[['shortsword', 2, 2, 6]])

antijoe = Creature("antiJoe", "evil",
                    ac=17, hp=103, #bog standard leather-clad level 3.
                    attack_parameters=[['shortsword', 2, 2, 6]])

hero = Creature("hero", "good",
                    ac=16, hp=18, #bog standard shielded leather-clad level 3.
                    attack_parameters=[['longsword', 4, 2, 8]])

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

anky=Creature("Ankylosaurus",
              ac=15, hp=68, alignment='evil',
              attack_parameters=[['tail',7,4,6,6,6,6]],
              log="CR 3 700 XP")

allo= Creature("Allosaurus","evil",
               ac=13, hp=51,
               attack_parameters=[['claw',6,4,8],['bite',6,4,10,10]])

polar= Creature("polar bear",'evil',
                ac=12, hp=42,
                attack_parameters=[['bite',7,5,8],['claw',7,5,6,6]])

test = Creature("Test", "good",
                    ac=10, hp=100,
                    attack_parameters=[['club', 2, 0, 4]])

inert = Creature("Test", "bad",
                    ac=10, hp=20,
                    attack_parameters=[['toothpick', 0, 0, 2]])

##################################################################
################### HERE IS WHERE YOU CAN DECIDE THE LINE UP #####

rounds = 100

wwe=Encounter(netsharpshooter,druid,barbarian,mega_tank,polar.copy(),polar.copy(),polar.copy())
print(wwe.go_to_war(rounds))

### KILL PEACEFULLY
import sys

sys.exit(0)
#ANYTHING AFTER THIS WILL BE DISREGARDED

###DUMPYARD ###########
#CODE HERE MAY BE BROKEN
