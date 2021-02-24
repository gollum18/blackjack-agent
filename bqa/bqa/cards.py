import random
from dataclasses import dataclass


@dataclass
class Card:
    suit: str
    face: int

    def __hash__(self):
        return hash((self.suit, self.face))


    def __eq__(self, other):
        if not isinstance(other, Card): return False
        return self.face == other.face and self.suit == other.suit


    def __str__(self):
        return '{} of {}'.format(
            self.face_as_str(), 
            self.suit_as_str()
        )


    def card_as_str(self):
        return self.__str__()


    def face_value(self):
        if self.face == 11:
            return 10
        elif self.face == 12:
            return 10
        elif self.face == 13:
            return 10
        else:
            return self.face


    def face_as_str(self):
        if self.face == 1:
            return 'A'
        elif self.face == 11:
            return 'J'
        elif self.face == 12:
            return 'Q'
        elif self.face == 13:
            return 'K'
        else:
            return str(self.face)


    def suit_as_str(self):
        return self.suit


class Deck:

    def __init__(self):
        self._cards = [
            Card(suit, face) 
            for suit in ['H', 'S', 'D', 'C'] 
            for face in range(1, 14)
        ]
        random.shuffle(self._cards)


    def __len__(self):
        return len(self._cards)


    def draw(self) -> Card:
        return self._cards.pop()


    def reshuffle(self, discard: list):
        self._cards.extend(discard)
        random.shuffle(self._cards)
