from bqa.cards import Card, Deck

import unittest


class TestCard(unittest.TestCase):
    pass


class TestDeck(unittest.TestCase):


    def test_str(self):
        deck = Deck()
        while deck:
            card = deck.draw()
            print(card)
        return True

    
    def test_draw(self):
        deck = Deck()
        while deck:
            card = deck.draw()
            self.assertTrue(isinstance(card, Card))
        self.assertEqual(len(deck), 0)


    def test_reshuffle(self):
        deck = Deck()
        discard = []
        for i in range(10):
            discard.append(deck.draw())
        self.assertEqual(len(deck), 42)
        deck.reshuffle(discard)
        self.assertEqual(len(deck), 52)
