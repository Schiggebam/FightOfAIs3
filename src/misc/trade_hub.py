from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set

from src.ai.AI_MapRepresentation import AI_Trade
from src.misc.game_constants import TradeType, TradeCategory, TradeState, hint, debug
from src.player import Player


@dataclass
class Trade:
    owner: int
    type: TradeType
    offer: (TradeCategory, int)
    demand: (TradeCategory, int)
    target_id: int = -1
    life_time = 3       # default lifetime for a Trade (3 turns)


class TradeHub:
    __id: int = 0

    def __init__(self):
        self.trades: Dict[int, Trade] = {}

    def handle_ai_output(self, output: List[AI_Trade], player: Player, player_list):
        """handles the output of the AI"""
        for trade in output:
            if trade.state is TradeState.ACCEPTED:
                tid, valid_trade = self.__get_trade(trade)
                if trade.target_id == -1 or trade.target_id == player.id:
                    if valid_trade:
                        if TradeHub.handle_trade(valid_trade, player, player_list):
                            del self.trades[tid]
            if trade.state is TradeState.NEW:
                accepted = True
                if trade.type is TradeType.OFFER or trade.type is TradeType.GIFT:
                    accepted = TradeHub.balance(trade.offer[0], player, -trade.offer[1])
                if accepted:
                    self.trades[TradeHub.get_next_id()] = Trade(player.id, trade.type, trade.offer,
                                                                trade.demand, trade.target_id)
            if trade.state is TradeState.REFUSED:
                tid, valid_trade = self.__get_trade(trade)
                if valid_trade:
                    del self.trades[tid]
            if trade.state is TradeState.OPEN:
                pass

    def next_turn(self, player_list: List[Player]):
        """will sort out old events"""
        to_be_deleted: Set[int] = set()
        for tid, trade in self.trades.items():
            trade.life_time -= 1
            if trade.life_time <= 0:
                if trade.type is TradeType.OFFER or trade.type is TradeType.GIFT:
                    TradeHub.balance(trade.offer[0], player_list[trade.owner], +trade.offer[1])
                to_be_deleted.add(tid)
        for tbd in to_be_deleted:
            del self.trades[tbd]


    def get_trades_for_ai(self, current_player: int) -> List[AI_Trade]:
        """generates a list of AI_trades which are significant for the respective player"""
        ret = []
        for tid, trade in self.trades.items():
            if trade.target_id == -1 or trade.target_id == current_player:
                ret.append(AI_Trade(trade.owner, trade.type, trade.offer, trade.demand, TradeState.OPEN))
        return ret

    @staticmethod
    def handle_trade(trade: Trade, player: Player, player_list: List[Player]) -> bool:
        if trade.owner == player.id:
            hint(f"cannot accept own trades -> trade will be deleted [{trade.owner}, [{player.id}]]")
            return False
        else:
            other_player = player_list[trade.owner]
            if trade.type is TradeType.OFFER:
                if not TradeHub.balance(trade.demand[0], player, -trade.demand[1]):
                    return False    # player could not balance
                # owner will receive demand, at lose the offer
                TradeHub.balance(trade.demand[0], other_player, +trade.demand[1])
                # current player will receive the offer and play the demand
                TradeHub.balance(trade.demand[0], player, -trade.demand[1])
                TradeHub.balance(trade.offer[0], player, +trade.offer[1])

            else:
                amount = 0
                trade_cat = None
                if trade.type is TradeType.GIFT:
                    amount = trade.offer[1]
                    trade_cat = trade.offer[0]
                elif trade.type is TradeType.CLAIM:
                    amount = - trade.demand[1]
                    trade_cat = trade.demand[0]

                TradeHub.balance(trade_cat, player, amount)
        return True

    def __get_trade(self, ai_trade: AI_Trade) -> Optional[Tuple[int, Trade]]:
        for tid, trade in self.trades.items():
            if trade.owner == ai_trade.owner_id:
                if trade.offer == ai_trade.offer and trade.demand == ai_trade.demand:
                    if trade.type == ai_trade.type:
                        return tid, trade
        return None

    @staticmethod
    def balance(tc: TradeCategory, p: Player, diff: int):
        if tc is TradeCategory.RESOURCE:
            if diff + p.amount_of_resources > 0:
                p.amount_of_resources += diff
            else:
                return False
        if tc is TradeCategory.FOOD:
            if diff + p.food > 0:
                p.food += diff
            else:
                return False
        if tc is TradeCategory.CULTURE:
            if diff + p.culture > 0:
                p.culture += diff
            else:
                return False
        return True

    @staticmethod
    def get_next_id():
        TradeHub.__id += 1
        return TradeHub.__id

    def print_active_trades(self):
        debug("Current Trades:")
        for tid, trade in self.trades.items():
            debug(f"ID: {tid}, T: {trade.owner}, {trade.type.name}, {trade.offer}, {trade.demand} LT: {trade.life_time}.")
