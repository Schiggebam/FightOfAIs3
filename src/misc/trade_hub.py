# from dataclasses import dataclass
# from typing import List
#
# from src.misc.game_constants import OfferType
#
#
# @dataclass
# class Gift:
#     sender_id: int
#     receiver_id: int
#     resources: int
#     culture: int
#
# @dataclass
# class Offer:
#     sender_id: int
#     receiver_id: int
#     offer_type: OfferType
#     wanted: int
#     offered: int
#
# class TradeHub:
#     def __init__(self):
#         self.gifts: List[Gift] = []
#         self.offers: List[Offer] = []
#
#     def update(self):
#         pass