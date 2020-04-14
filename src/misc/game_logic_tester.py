from src.game_accessoires import Army, Unit
from src.misc.game_constants import UnitType
from src.misc.game_logic_misc import FightCalculator


def print_army(army: Army):
    print("({}|{}|{})".format(army.get_population_by_unit(UnitType.MERCENARY),
                                        army.get_population_by_unit(UnitType.KNIGHT),
                                        army.get_population_by_unit(UnitType.BABARIC_SOLDIER)))


def sim_fight(attacker_constellation, defender_constellation):
    attacker: Army = Army(None, 0)
    defender: Army = Army(None, 0)
    c = 0
    for ut in UnitType:
        for i in range(attacker_constellation[c]):
            unit: Unit = Unit(ut)
            attacker.add_unit(unit)
        for j in range(defender_constellation[c]):
            unit: Unit = Unit(ut)
            defender.add_unit(unit)
        c = c + 1
    print("\n \n")
    print_army(attacker)
    print_army(defender)
    FightCalculator.army_vs_army(attacker, defender)
    print("aftermath:")
    print_army(attacker)
    print_army(defender)


# setup
Unit.unit_info = [(UnitType.MERCENARY, {'name': "", 'attack': int(3), 'defence': int(1), 'population': int(1),
                                        'cost_resource': 1, 'cost_culture': 1}),
                  (UnitType.KNIGHT, {'name': "", 'attack': int(2), 'defence': int(4), 'population': int(1),
                                     'cost_resource': 1, 'cost_culture': 1}),
                  (UnitType.BABARIC_SOLDIER, {'name': "", 'attack': int(1), 'defence': int(2), 'population': int(1),
                                              'cost_resource': 1, 'cost_culture': 1})]

attacker_constellation = (5, 1, 0)
defender_constellation = (1, 3, 0)
sim_fight(attacker_constellation, defender_constellation)

attacker_constellation = (10, 0, 0)
defender_constellation = (0, 9, 0)
sim_fight(attacker_constellation, defender_constellation)

attacker_constellation = (41, 0, 0)
defender_constellation = (0, 30, 0)
sim_fight(attacker_constellation, defender_constellation)
