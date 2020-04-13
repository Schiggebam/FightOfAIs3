import queue
from math import ceil

from src.game_accessoires import Army
from src.misc.building import Building
from src.misc.game_constants import BuildingType, BuildingState, LogType, DiploEventType, UnitType, hint
from src.player import Player


class IncomeCalculator:
    def __init__(self, hex_map, scenario):
        self.scenario = scenario  # reference to scenario
        self.hex_map = hex_map  # reference to hex_map

    def calculate_income(self, player: Player) -> int:
        if player.is_barbaric:
            return 1  # linear growth for barbaric players
        income = int(0)
        for building in player.buildings:
            if building.building_state == BuildingState.UNDER_CONSTRUCTION:
                continue
            if building.building_state == BuildingState.DESTROYED:
                continue
            income = income + building.resource_per_turn
            for tile in self.hex_map.get_neighbours(building.tile):
                for res in self.scenario.resource_list:
                    if res.tile.offset_coordinates == tile.offset_coordinates:
                        income = income + res.demand_res(building.resource_per_field)

        return income

    def calculate_food(self, player: Player) -> int:
        food_inc = 0
        if player.is_barbaric:
            return 0  # no food mechancis for barbaric players
        for building in player.buildings:
            if building.construction_time > 0:
                continue
            if building.building_type == BuildingType.FARM:
                food_inc = food_inc + len(building.associated_tiles)
            else:
                food_inc = food_inc - building.food_consumption
        return food_inc

    def calculate_culture(self, player: Player) -> int:
        c = int(0)
        for building in player.buildings:
            c = c + building.culture_per_turn
        return c


class FightCalculator:



    @staticmethod
    def army_vs_army(attacker: Army, defender: Army):
        attack_value = attacker.get_attack_strength()
        defencive_value = defender.get_defence_strength()
        attacker_won = attack_value >= defencive_value          # they can both win if their values are equal
        defender_won = defencive_value >= attack_value
        attacker_losses = defencive_value if attacker_won else attack_value
        defender_losses = 0 if defender_won else defencive_value
        attacker_alive_pop_ratio = (attack_value - attacker_losses) / attack_value
        defender_alive_pop_ratio = (defencive_value - defender_losses) / defencive_value
        if attacker_won:
            attacker_alive_pop_ratio = attacker_alive_pop_ratio + (attacker_losses/3.0) / attack_value
        if defender_won:
            defender_alive_pop_ratio = defender_alive_pop_ratio + (defender_losses/3.0) / defencive_value
        attacker_pop = attacker.get_population()
        defender_pop = defender.get_population()
        attacker_surviving_pop_ratio = attacker_pop * attacker_alive_pop_ratio
        defender_surviving_pop_ratio = defender_pop * defender_alive_pop_ratio
        for unit in UnitType:
            attacker_unit_x = attacker.get_population_by_unit(unit)
            attacker_kill_count_unit_x = attacker_unit_x - ((attacker_unit_x / attacker_pop) *
                                                            attacker_surviving_pop_ratio)
            attacker.remove_units_of_type(ceil(attacker_kill_count_unit_x), unit)
            defender_unit_x = defender.get_population_by_unit(unit)
            defender_kill_count_unit_x = defender_unit_x - ((defender_unit_x / defender_pop) *
                                                            defender_surviving_pop_ratio)
            defender.remove_units_of_type(ceil(defender_kill_count_unit_x), unit)

    @staticmethod
    def army_vs_building(attacker: Army, defender: Building):
        attack_value = attacker.get_attack_strength()
        defencive_value = defender.defensive_value
        attacker_won = attack_value >= defencive_value  # they can both win if their values are equal
        defender_won = defencive_value >= attack_value
        if attacker_won:
            attacker_losses = defencive_value if attacker_won else attack_value
            attacker_alive_ratio = (attack_value - attacker_losses) / attack_value
            attacker_alive_ratio = attacker_alive_ratio + (attacker_losses / 3.0) / attack_value
            attacker_pop = attacker.get_population()
            attacker_surviving_pop_ratio = attacker_pop * attacker_alive_ratio
            for unit in UnitType:
                attacker_unit_x = attacker.get_population_by_unit(unit)
                attacker_kill_count_unit_x = attacker_unit_x - ((attacker_unit_x / attacker_pop) *
                                                                attacker_surviving_pop_ratio)
                attacker.remove_units_of_type(ceil(attacker_kill_count_unit_x), unit)
            defender.defensive_value = -1       # building is destroyed
        if defender_won:
            attacker.remove_all_units()         # army is destroyed




class Logger:
    class Log:
        def __init__(self, log_tpye):
            self.log_type = log_tpye

    class BattleLog(Log):
        def __init__(self, log_type: LogType, attacker_strength: int, defender_strength: int,
                     init_s_attacker: int, init_s_defender):
            super().__init__(log_type)
            self.after_attacker_strength: int = attacker_strength
            self.after_defender_strength: int = defender_strength
            self.init_strength_attacker: int = init_s_attacker
            self.init_strength_defender: int = init_s_defender

    class EventLog(Log, ):
        def __init__(self, log_type, event: int, relative_change: float, loc: (int, int), lifetime: int, player_name: str):
            super().__init__(log_type)
            self.event_type = event
            self.relative_change = relative_change
            self.loc = loc
            self.lifetime = lifetime
            self.player_name = player_name

    logs: queue.Queue = queue.Queue()

    @staticmethod
    def log_battle_army_vs_army_log(attacker: Army, defender: Army, attacker_initial_strength: int,
                                    defender_initial_strength: int):
        # log = Logger.BattleLog(LogType.BATTLE_ARMY_VS_ARMY, attacker.strength, defender.strength,
        #                        attacker_initial_strength, defender_initial_strength)
        # Logger.logs.put(log)
        raise NotImplementedError("Logger logged error:)")  # TODO implement this method

    @staticmethod
    def log_battle_army_vs_building(attacker: Army, defender: Building, attacker_initial_strength: int,
                                    defender_initial_strength: int):
        # log = Logger.BattleLog(LogType.BATTLE_ARMY_VS_BUILDING, attacker.strength, defender.defensive_value,
        #                        attacker_initial_strength, defender_initial_strength)
        # Logger.logs.put(log)
        raise NotImplementedError("Logger logged error:)")  # TODO implement this method

    @staticmethod
    def log_diplomatic_event(event: int, relative_change: float, loc: (int, int), lifetime: int, player_name:str):
        if event == DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED or \
                event == DiploEventType.TYPE_ENEMY_ARMY_INVADING:
            log = Logger.EventLog(LogType.DIPLO_ENEMY_BUILDING_SCOUTED,
                                  event, relative_change, loc, lifetime, player_name)
            Logger.logs.put(log)

