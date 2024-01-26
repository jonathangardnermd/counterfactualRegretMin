import unittest
from good_cfr import getDecidingPlayerForInfoSetStr, playerOnePocketIsHigher

# just a simple and mostly-worthless example of how you'd include unit tests for this, but what's the fun in writing tests unless someone's paying you for it?! ;)
class TestGetDecidingPlayer(unittest.TestCase):
    def test_getDecidingPlayer(self):
        # Test case for 'Kpb': player 1 decision
        result = getDecidingPlayerForInfoSetStr('Kpb')
        self.assertEqual(result, 0, "Expected player 1 to be the deciding player for 'Kpb'")

        # Test case for 'Kp': player 2 decision
        result = getDecidingPlayerForInfoSetStr('Kp')
        self.assertEqual(result, 1, "Expected player 2 to be the deciding player for 'Kp'")

    def test_playerOnePocketIsHigher(self):
        # Test case: 'K' pocket is higher than 'Q' pocket
        result = playerOnePocketIsHigher('K', 'Q')
        self.assertTrue(result, "Expected 'K' pocket to be higher than 'Q' pocket")

        # Test case: 'J' pocket is not higher than 'Q' pocket
        result = playerOnePocketIsHigher('J', 'Q')
        self.assertFalse(result, "Expected 'J' pocket to not be higher than 'Q' pocket")

if __name__ == '__main__':
    unittest.main()
