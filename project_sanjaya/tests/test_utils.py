import unittest
import os
import json
from project_sanjaya.backend import utils

class TestUtils(unittest.TestCase):

    def test_haversine(self):
        # Test with known values
        lat1, lon1 = 34.0522, -118.2437  # Los Angeles
        lat2, lon2 = 34.0522, -118.2437  # Same point
        self.assertAlmostEqual(utils.haversine(lat1, lon1, lat2, lon2), 0.0, places=2)

        lat2, lon2 = 40.7128, -74.0060  # New York
        # Known distance is approx 3935 km
        self.assertAlmostEqual(utils.haversine(lat1, lon1, lat2, lon2) / 1000, 3935.7, places=0)

    def test_generate_session_hash(self):
        username = "testuser"
        hash1 = utils.generate_session_hash(username)
        hash2 = utils.generate_session_hash(username)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)
        self.assertNotEqual(hash1, hash2)

    def test_increment_api_usage(self):
        api_name = "test_api"
        path = "project_sanjaya/logs/api_usage.json"

        # Clean up previous test runs
        if os.path.exists(path):
            os.remove(path)

        # First increment
        self.assertEqual(utils.increment_api_usage(api_name), 1)
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data[api_name], 1)

        # Second increment
        self.assertEqual(utils.increment_api_usage(api_name), 2)
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data[api_name], 2)

        if os.path.exists(path):
            os.remove(path)

if __name__ == '__main__':
    unittest.main()
