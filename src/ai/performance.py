from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

from src.ai.AI_MapRepresentation import Map
from src.game_accessoires import Unit
from src.misc.building import Building
from src.misc.game_constants import UnitType, BuildingType


class ScoreSpentResources:
    """computes a score for the AI:
    This score is only based on spent resources"""

    @staticmethod
    def evaluate(map: Map) -> int:
        used_resources = 0
        for b in map.building_list:
            # ! if a building is upgraded, count also its lower levels
            if b.type == BuildingType.CAMP_3:
                used_resources += Building.get_construction_cost(BuildingType.CAMP_2)
                used_resources += Building.get_construction_cost(BuildingType.CAMP_1)
            if b.type == BuildingType.CAMP_2:
                used_resources += Building.get_construction_cost(BuildingType.CAMP_1)
            used_resources += Building.get_construction_cost(b.type)

        for a in map.army_list:
            cost_knight = Unit.get_unit_cost(UnitType.KNIGHT)
            cost_merc = Unit.get_unit_cost(UnitType.MERCENARY)
            cost_bar = Unit.get_unit_cost(UnitType.BABARIC_SOLDIER)
            used_resources += a.knights * (cost_knight.resources + cost_knight.culture)
            used_resources += a.mercenaries * (cost_merc.resources + cost_merc.culture)
            used_resources += a.barbaric_soldiers * (cost_bar.resources + cost_bar.culture)

        used_resources += len(map.discovered_tiles)
        return used_resources


@dataclass
class PerfomanceLog:
    turn_nr: int
    score: int


class PerformanceLogger:
    """can print the performance to a csv file """

    data: Dict[int, List[PerfomanceLog]] = {}
    pid_c: List[Tuple[int, str]] = []

    @staticmethod
    def setup(player_ids_and_colours: List[Tuple[int, str]]):
        for pid, c in player_ids_and_colours:
            PerformanceLogger.data[pid] = []
            PerformanceLogger.pid_c.append((pid, PerformanceLogger.__colour_to_numpy_code(c)))

    @staticmethod
    def log_performance_file(turn_nr: int, player_id: int, score: int):
        PerformanceLogger.data[player_id].append(PerfomanceLog(turn_nr, score))

    @staticmethod
    def show():
        y = []
        x = []
        y_idx = 0
        for pid, logs in PerformanceLogger.data.items():
            y.append([])
            for log in logs:
                if y_idx == 0:
                    x.append(log.turn_nr)
                y[y_idx].append(log.score)
            y_idx += 1
        if y_idx == 1:
            plt.plot(x, y[0])
        elif y_idx == 2 or y_idx == 3:
            x = x[:len(y[1])]
            y1 = y[0][:len(y[1])]
            y2 = y[1][:len(y[1])]
            c1 = PerformanceLogger.pid_c[0][1]
            c2 = PerformanceLogger.pid_c[1][1]
            if y_idx == 3:
                x = x[:len(y[2])]
                y1 = y[0][:len(y[2])]
                y2 = y[1][:len(y[2])]
                y3 = y[2][:len(y[2])]
                c3 = PerformanceLogger.pid_c[2][1]
                plt.plot(x, y1, c1, x, y2, c2, x, y3, c3)
                plt.show()
            else:
                plt.plot(x, y1, c1, x, y2, c2)
                plt.show()



    @staticmethod
    def __colour_to_numpy_code(code: str) -> str:
        if code == "red":
            return 'r'
        if code == "blue":
            return 'b'
        if code == "green":
            return 'g'
        if code == "yellow":
            return 'y'
