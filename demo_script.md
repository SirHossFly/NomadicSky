# NomadicSky MVP Demo Script

This demo script showcases the key features of NomadicSky, a conversational weather assistant designed for nomads/rv'ers. The script simulates a planning a week-long trip, using the agent to check current weather, historical trends, forecasts, and personalized recommendations based on preferences.

## Scenario: Planning a Week-Long Nomad Trip

**User (Nomad)**: I'm a nomad planning to travel through the U.S. next week. I prefer warm, sunny weather and want to visit Knoxville and Tucson. Let’s set up my preferences and plan my trip.

### Step 1: Set Preferences
**Query**: "I like Knoxville"  
**Expected Response**: "Got it! I've added Knoxville to your preferred cities."

**Query**: "I like Tucson"  
**Expected Response**: "Got it! I've added Tucson to your preferred cities."

**Query**: "I like sunny weather"  
**Expected Response**: "Got it! I've updated your preferences to favor sunny weather."

**Query**: "I prefer warm weather"  
**Expected Response**: "Got it! I've updated your preference for warm weather."

**Query**: "What are my preferences?"  
**Expected Response**:  
- Preferred cities: Knoxville, Tucson  
- Temperature preference: warm weather  
- Weather condition preference: sunny

### Step 2: Check Current Weather
**Query**: "What's the weather in my preferred cities?"  
**Expected Response**:  
- Knoxville: 62°F, mist (too cool for your warm preference) (not sunny)  
- Tucson: 73°F, scattered clouds (too cool for your warm preference) (not sunny)  
(Note: Actual weather data will vary based on the date of testing.)

### Step 3: Review Historical Weather for Planning
**Query**: "What were the average highs and lows in Knoxville in June?"  
**Expected Response**:  
In Knoxville for June 2024, the average high temperature was about 83°F, and the average low was around 56°F. That's a pretty pleasant summer month with warm days and cool nights—perfect for nomad adventures!  
(Note: Historical data availability varies; may return "no data found" if unavailable.)

**Query**: "What were the average highs and lows in Tucson in December?"  
**Expected Response**:  
Based on the historical weather data for Tucson in December 2024, the average high temperature was about 58°F, and the average low was around 33°F. That makes for some mild days and chilly nights—perfect for nomads to pack layers and enjoy the desert vibes without the summer heat.

### Step 4: Check Forecast for Next Week
**Query**: "What's the forecast for my preferred cities?"  
**Expected Response**:  
**Knoxville Forecast:**  
- June 4: Avg 73°F (High 86°F, Low 62°F), Clear sky – Too cool for your warm preference.  
- June 5: Avg 75°F (High 85°F, Low 65°F), Overcast clouds – Too cool, not sunny.  
- June 6: Avg 76°F (High 88°F, Low 67°F), Clear sky – Matches your preferences!  
- June 7: Avg 72°F (High 81°F, Low 68°F), Light rain – Too cool, not sunny.  
- June 8: Avg 72°F (High 85°F, Low 66°F), Moderate rain – Too cool, not sunny.  
**Tucson Forecast:**  
- June 4: Avg 82°F (High 95°F, Low 73°F), Scattered clouds – Not sunny.  
- June 5: Avg 84°F (High 92°F, Low 77°F), Clear sky – Matches your preferences!  
- June 6: Avg 87°F (High 95°F, Low 79°F), Clear sky – Matches your preferences!  
- June 7: Avg 89°F (High 97°F, Low 80°F), Clear sky – Matches your preferences!  
- June 8: Avg 90°F (High 98°F, Low 81°F), Clear sky – Matches your preferences!  
(Note: Forecast data will vary.)

### Step 5: Make a Decision with Combined Insights
**Query**: "Compare the weather in Knoxville and Tucson this week."  
**Expected Response**:  
**Knoxville Forecast:**  
- June 4: Avg 73°F (High 86°F, Low 62°F), Clear sky – Too cool for your warm preference.  
- June 5: Avg 75°F (High 85°F, Low 65°F), Overcast clouds – Too cool, not sunny.  
- June 6: Avg 76°F (High 88°F, Low 67°F), Clear sky – Matches your preferences!  
- June 7: Avg 72°F (High 81°F, Low 68°F), Light rain – Too cool, not sunny.  
- June 8: Avg 72°F (High 85°F, Low 66°F), Moderate rain – Too cool, not sunny.  
**Tucson Forecast:**  
- June 4: Avg 82°F (High 95°F, Low 73°F), Scattered clouds – Not sunny.  
- June 5: Avg 84°F (High 92°F, Low 77°F), Clear sky – Matches your preferences!  
- June 6: Avg 87°F (High 95°F, Low 79°F), Clear sky – Matches your preferences!  
- June 7: Avg 89°F (High 97°F, Low 80°F), Clear sky – Matches your preferences!  
- June 8: Avg 90°F (High 98°F, Low 81°F), Clear sky – Matches your preferences!  
Tucson looks like the better spot this week if you’re chasing warmth and sun. Knoxville has some nice days but might be cooler and wetter overall.

## Conclusion
NomadicSky helps nomads/rv'ers like you plan trips by providing current weather, historical trends, forecasts, and personalized recommendations based on your preferences. In this demo, Tucson emerged as the better choice for a warm, sunny week-long trip. You can now run `nomadicsky.py` to interact with the agent and plan your own adventures!