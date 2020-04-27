from typing import Dict, Any
from src.misc.game_constants import UnitType, BuildingType, ResourceType

import untangle


class GameFileReader:
    def __init__(self, xml_game_data: str):
        self.xml_parser = untangle.parse(xml_game_data)

    def read_textures_to_dict(self, tex_dict: {}):
        for elem in self.xml_parser.game.textures.children:
            tex_dict[elem.get_attribute('code')] = (elem.cdata,
                                                    int(elem.get_attribute('offsetX')),
                                                    int(elem.get_attribute('offsetY')),
                                                    float(elem.get_attribute('scale')))

    def read_map(self, map_list: [str]):
        raw: str = self.xml_parser.game.map.cdata
        row_wise: [str] = raw.strip().splitlines()
        row_wise.reverse()
        for row in row_wise:
            map_list.append(row.split())

    def read_map_obj(self, map_obj_list: [(str, int, int)]):
        """fills the list with the strcode, as well as the position in offset coordinates"""
        raw: str = self.xml_parser.game.map_obj.cdata
        row_wise: [str] = raw.strip().splitlines()
        row_wise.reverse()
        for y in range(len(row_wise)):
            s_split = row_wise[y].split()
            for x in range(len(s_split)):
                if s_split[x] != "--":
                    map_obj_list.append((s_split[x], x, y))

    def read_resource_info(self, resource_info: Dict[ResourceType, Dict[str, Any]]):
        for elem in self.xml_parser.game.resources.children:
            from src.misc.game_constants import ResourceType
            resource_info[ResourceType.get_type_from_strcode(elem.get_attribute('code'))] = {
                'amount': int(elem.get_attribute('amount'))}

    def read_building_info(self, building_info: Dict[BuildingType, Dict[str, Any]]):
        for elem in self.xml_parser.game.buildings.children:
            building_info[BuildingType.get_type_from_strcode(elem.get_attribute('code'))] = {
                'tex_code': elem.get_attribute('code'),
                'construction_cost': int(elem.get_attribute('construction_cost')),
                'culture_per_turn': int(elem.get_attribute('culture_per_turn')),
                'resource_per_field': int(elem.get_attribute('resource_per_field')),
                'resource_per_turn': int(elem.get_attribute('resource_per_turn')),
                'sight_range': int(elem.get_attribute('sight_range')),
                'food_consumption': int(elem.get_attribute('food_consumption')),
                'construction_time': int(elem.get_attribute('construction_time')),
                'defensive_value': int(elem.get_attribute('defensive_value')),
                'flag_x': int(elem.get_attribute('flag_x')),
                'flag_y': int(elem.get_attribute('flag_y')),
                'grant_pop': int(elem.get_attribute('grant_pop')),
                'description': elem.cdata}

    def read_player_info(self, player_info: [(str, {})]):
        for elem in self.xml_parser.game.players.children:
            player_info.append((elem.cdata,
                                {'colour' : elem.get_attribute('colour'),
                                 'spawn_x': int(elem.get_attribute('spawn_x')),
                                 'spawn_y': int(elem.get_attribute('spawn_y')),
                                 'ai'     : elem.get_attribute('ai'),
                                 'army_rel_to_spawn_x': int(elem.get_attribute('army_rel_to_spawn_x')),
                                 'army_rel_to_spawn_y': int(elem.get_attribute('army_rel_to_spawn_y'))}))

    def read_unit_info(self, unit_info: Dict[UnitType, Dict[str, Any]]):
        for elem in self.xml_parser.game.units.children:
            unit_info[UnitType.get_type_from_strcode(elem.get_attribute('code'))] = {
                'attack': int(elem.get_attribute('attack')),
                'defence': int(elem.get_attribute('defence')),
                'name': elem.get_attribute('name'),
                'population': int(elem.get_attribute('population')),
                'cost_resource': int(elem.get_attribute('cost_resource')),
                'cost_culture': int(elem.get_attribute('cost_culture')),
                'description': elem.cdata}


