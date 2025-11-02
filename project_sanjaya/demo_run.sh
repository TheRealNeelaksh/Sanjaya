#!/bin/bash

# This script simulates a trip by sending a series of location updates to the backend.
# Make sure the backend server is running before executing this script.

API_URL="http://127.0.0.1:8000"
TEST_USERNAME="demochild"
TEST_PASSWORD="password"

echo "Registering a test user..."
curl -X POST "$API_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"password\": \"$TEST_PASSWORD\", \"role\": \"child\"}"

echo "\n\nLogging in to get a token..."
TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"password\": \"$TEST_PASSWORD\"}")
TOKEN=$(echo $TOKEN_RESPONSE | jq -r .access_token)

echo "\n\nStarting a new trip..."
TRIP_RESPONSE=$(curl -s -X POST "$API_URL/start_trip" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"mode\": \"road\"}")
SESSION_HASH=$(echo $TRIP_RESPONSE | jq -r .session_hash)

echo "\n\nStarting trip simulation..."
LAT=34.0
LON=-118.0
for i in {1..10}
do
    echo "Sending location update #$i..."
    curl -X POST "$API_URL/update_location" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"session_hash\": \"$SESSION_HASH\", \"lat\": $LAT, \"lon\": $LON, \"battery\": 90.0}"

    LAT=$(echo "$LAT + 0.01" | bc)
    LON=$(echo "$LON + 0.01" | bc)
    sleep 2
done

echo "\n\nTrip simulation complete."
