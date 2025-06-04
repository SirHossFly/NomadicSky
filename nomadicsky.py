import requests
from langchain.tools import Tool
from langchain_xai import ChatXAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
import json

# Load API keys from api_keys.txt
def load_api_key(key_name):
    with open("api_keys.txt", "r") as file:
        for line in file:
            if line.startswith(key_name):
                return line.split("=")[1].strip()
    raise ValueError(f"{key_name} not found in api_keys.txt")

OPENWEATHERMAP_API_KEY = load_api_key("OPENWEATHERMAP_API_KEY")
GROK3_API_KEY = load_api_key("GROK3_API_KEY")
NOAA_API_KEY = load_api_key("NOAA_API_KEY")

# Functions to manage user preferences
def read_user_prefs():
    try:
        with open("user_prefs.json", "r") as file:
            prefs = json.load(file)
            # Validate existing cities
            if "preferred_cities" in prefs:
                valid_cities = []
                for city in prefs["preferred_cities"]:
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}"
                    response = requests.get(url)
                    if response.status_code == 200:
                        valid_cities.append(city)
                prefs["preferred_cities"] = valid_cities
                write_user_prefs(prefs)  # Save updated preferences
            return prefs
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, return default structure
        return {"preferred_cities": [], "temperature_preference": None, "weather_condition_preference": None}

def write_user_prefs(prefs):
    with open("user_prefs.json", "w") as file:
        json.dump(prefs, file, indent=4)

# Function to fetch current weather from OpenWeatherMap
def get_current_weather(location):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHERMAP_API_KEY}&units=imperial"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        city = data["name"]
        return {"city": city, "temp": temp, "description": description}
    else:
        return {"error": f"Error fetching weather for {location}: {response.status_code}"}
    
# Function to fetch 5-day weather forecast from OpenWeatherMap
def get_weather_forecast(location):
    # First, get coordinates for the location
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHERMAP_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        # Suggest preferred cities if available
        prefs = read_user_prefs()
        preferred_cities = prefs.get("preferred_cities", [])
        suggestion = f"Try a different city, like {', '.join(preferred_cities)} if you have any preferred cities set." if preferred_cities else "Try a different city, like 'Knoxville' or 'Tucson'."
        return {"error": f"Could not find coordinates for {location}: {response.status_code}. {suggestion}"}
    data = response.json()
    lat = data["coord"]["lat"]
    lon = data["coord"]["lon"]
    city = data["name"]

    # Fetch 5-day forecast (3-hourly data for 5 days = 40 data points)
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}&units=imperial"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": f"Error fetching forecast for {city}: {response.status_code}"}

    data = response.json()
    if "list" not in data or not data["list"]:
        return {"error": f"No forecast data found for {city}."}

    # Process forecast: summarize daily averages, highs, and lows
    daily_forecasts = {}
    for entry in data["list"]:
        # Extract date (e.g., "2025-06-04 12:00:00" -> "2025-06-04")
        date = entry["dt_txt"].split(" ")[0]
        temp = entry["main"]["temp"]
        description = entry["weather"][0]["description"]

        if date not in daily_forecasts:
            daily_forecasts[date] = {"temps": [], "descriptions": []}
        daily_forecasts[date]["temps"].append(temp)
        daily_forecasts[date]["descriptions"].append(description)

    # Summarize each day: average, high, low temperature, most frequent weather description
    forecast_summary = []
    for date, info in daily_forecasts.items():
        temps = info["temps"]
        avg_temp = sum(temps) / len(temps)
        high_temp = max(temps)
        low_temp = min(temps)
        # Get most frequent weather description
        description_counts = {}
        for desc in info["descriptions"]:
            description_counts[desc] = description_counts.get(desc, 0) + 1
        most_frequent_desc = max(description_counts, key=description_counts.get)
        forecast_summary.append({
            "date": date,
            "avg_temp": round(avg_temp, 2),
            "high_temp": round(high_temp, 2),
            "low_temp": round(low_temp, 2),
            "description": most_frequent_desc
        })

    return {"city": city, "forecast": forecast_summary}

# Function to find warm places
def find_warm_places(query):
    cities = ["Knoxville,TN,US", "Tucson,AZ,US", "Austin,TX,US", "Portland,OR,US", "Miami,FL,US"]
    weather_data = []
    for city in cities:
        result = get_current_weather(city)
        if "error" not in result:
            weather_data.append(result)
        else:
            print(result["error"])
    warm_places = [data for data in weather_data if data["temp"] >= 75.0]
    warm_places.sort(key=lambda x: x["temp"], reverse=True)
    if warm_places:
        response = "Here are some warm places:\n"
        for place in warm_places:
            response += f"- {place['city']}: {place['temp']}°F, {place['description']}\n"
        return response.strip()
    else:
        return "No warm places found (temperature >= 75°F)."

# Function to fetch historical weather highs and lows from NOAA API
def get_historical_weather(location_month):
    # Parse input (e.g., "Knoxville June")
    try:
        location, month = location_month.split()
    except ValueError:
        return {"error": "Please provide a location and month (e.g., 'Knoxville June')."}

    # Map month to numeric value (e.g., June -> 06)
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12"
    }
    month = month.lower()
    if month not in month_map:
        return {"error": f"Invalid month: {month}. Use full month name (e.g., 'June')."}
    month_num = month_map[month]

    # Use a fixed year for historical data (e.g., 2024, most recent full year)
    year = "2024"
    start_date = f"{year}-{month_num}-01"
    end_date = f"{year}-{month_num}-30"  # Simplified, assumes 30 days

    # First, get location coordinates from OpenWeatherMap (NOAA API uses lat/lon)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHERMAP_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": f"Could not find coordinates for {location}: {response.status_code}"}
    data = response.json()
    lat = data["coord"]["lat"]
    lon = data["coord"]["lon"]
    city = data["name"]

    # Fetch historical weather from NOAA (TMAX for highs, TMIN for lows)
    url = f"https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&datatypeid=TMAX,TMIN&locationid=FIPS:US&startdate={start_date}&enddate={end_date}&limit=1000"
    headers = {"token": NOAA_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"Error fetching historical weather for {city}: {response.status_code}"}

    data = response.json()
    if "results" not in data or not data["results"]:
        return {"error": f"No historical weather data found for {city} in {month} {year}."}

    # Calculate average highs (TMAX) and lows (TMIN) (values in tenths of °C, convert to °F)
    highs = [entry["value"] for entry in data["results"] if entry["datatype"] == "TMAX"]
    lows = [entry["value"] for entry in data["results"] if entry["datatype"] == "TMIN"]
    
    if not highs or not lows:
        return {"error": f"No high/low temperature data found for {city} in {month} {year}."}

    avg_high_c = sum(highs) / len(highs) / 10  # Convert from tenths of °C to °C
    avg_low_c = sum(lows) / len(lows) / 10    # Convert from tenths of °C to °C
    avg_high_f = (avg_high_c * 9/5) + 32      # Convert °C to °F
    avg_low_f = (avg_low_c * 9/5) + 32        # Convert °C to °F

    return {
        "city": city,
        "month": month.capitalize(),
        "year": year,
        "avg_high": round(avg_high_f, 2),
        "avg_low": round(avg_low_f, 2)
    }

# Create LangChain Tools
weather_tool = Tool(
    name="weather_lookup",
    func=get_current_weather,
    description="Fetches current weather for a given location. Input can be a city name (e.g., 'Knoxville') or city,state,country (e.g., 'Knoxville,TN,US')."
)

warm_places_tool = Tool(
    name="find_warm_places",
    func=find_warm_places,
    description="Finds warm places (temp >= 75°F) among nomad-friendly cities. Input can be any string (e.g., 'Find warm places')."
)

historical_weather_tool = Tool(
    name="historical_weather",
    func=get_historical_weather,
    description="Fetches historical weather highs and lows for a given location and month (e.g., 'Knoxville June'). Returns average high and low temperatures for that month in 2024."
)

forecast_weather_tool = Tool(
    name="forecast_weather",
    func=get_weather_forecast,
    description="Fetches a 5-day weather forecast for a given location, summarizing daily average temperature and most frequent weather condition. Input example: 'Knoxville'."
)

# Tool to update user preferences
def update_user_preferences(input_str):
    prefs = read_user_prefs()
    # Simple parsing: look for "I like [city/weather condition]" or "I prefer [temp] weather"
    if "I like" in input_str:
        input_part = input_str.split("I like", 1)[1].strip().lower()
        # Check for weather condition preference (e.g., "I like sunny weather")
        if "weather" in input_part:
            condition = input_part.split("weather")[0].strip()
            valid_conditions = ["sunny", "cloudy", "rainy", "clear"]
            if condition in valid_conditions:
                prefs["weather_condition_preference"] = condition
                write_user_prefs(prefs)
                return f"Got it! I've set your preferred weather condition to {condition}."
            else:
                return f"I didn't understand that weather condition. Try saying 'I like sunny weather' or 'I like rainy weather'."
        # Otherwise, assume it's a city (e.g., "I like Knoxville")
        else:
            city = input_str.split("I like", 1)[1].strip()
            # Validate city using OpenWeatherMap API
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}"
            response = requests.get(url)
            if response.status_code != 200:
                return f"I couldn't find {city} to add it to your preferred cities. Could you try a different city, like 'Knoxville' or 'Tucson', or double-check the spelling?"
            if city not in prefs["preferred_cities"]:
                prefs["preferred_cities"].append(city)
                write_user_prefs(prefs)
                return f"Got it! I've added {city} to your preferred cities."
            else:
                return f"{city} is already in your preferred cities!"
    elif "I prefer" in input_str and "weather" in input_str:
        # Extract temperature preference (e.g., "I prefer warm weather")
        temp_part = input_str.split("I prefer", 1)[1].split("weather")[0].strip()
        if "warm" in temp_part.lower():
            prefs["temperature_preference"] = "warm"
        elif "cool" in temp_part.lower() or "cold" in temp_part.lower():
            prefs["temperature_preference"] = "cool"
        else:
            return "I didn't understand your temperature preference. Try saying 'I prefer warm weather' or 'I prefer cool weather'."
        write_user_prefs(prefs)
        return f"Updated your temperature preference to {prefs['temperature_preference']} weather."
    else:
        return "I didn't understand your preference. Try saying 'I like Knoxville', 'I like sunny weather', or 'I prefer warm weather'."

update_preferences_tool = Tool(
    name="update_user_preferences",
    func=update_user_preferences,
    description="Updates user preferences, such as preferred cities, temperature preferences, or weather conditions. Validates cities before adding them. Input examples: 'I like Knoxville', 'I like sunny weather', 'I prefer warm weather'."
)

# Tool to retrieve user preferences
def get_user_preferences(query):
    prefs = read_user_prefs()
    preferred_cities = prefs.get("preferred_cities", [])
    temp_preference = prefs.get("temperature_preference", None)
    weather_condition_preference = prefs.get("weather_condition_preference", None)

    if not preferred_cities and not temp_preference and not weather_condition_preference:
        return "I don't have any preferences stored for you yet. You can tell me your preferences, like 'I like Knoxville', 'I prefer warm weather', or 'I like sunny weather'."

    # If the query explicitly asks for preferences, list them
    if "what are my preferences" in query.lower():
        response = "Here are your preferences:\n"
        if preferred_cities:
            response += f"- Preferred cities: {', '.join(preferred_cities)}\n"
        if temp_preference:
            response += f"- Temperature preference: {temp_preference} weather\n"
        if weather_condition_preference:
            response += f"- Weather condition preference: {weather_condition_preference}\n"
        return response.strip()

    # Proactively use preferences for weather-related queries
    response = ""
    if preferred_cities:
        # Handle forecast queries for preferred cities
        if "forecast" in query.lower():
            # Acknowledge variations like "this week"
            time_frame = "5-day"
            if "this week" in query.lower():
                time_frame = "next 5 days (this week's forecast)"
            response += f"Let me check the {time_frame} forecast for your preferred cities:\n"
            for city in preferred_cities:
                forecast_data = get_weather_forecast(city)
                if "error" in forecast_data:
                    response += f"- {city}: {forecast_data['error']}\n"
                    continue
                response += f"\n{city} forecast:\n"
                for day in forecast_data["forecast"]:
                    matches_preferences = True
                    mismatch_reason = ""
                    # Check if the day's average temperature matches the temperature preference
                    if temp_preference == "warm" and day["avg_temp"] < 75.0:
                        matches_preferences = False
                        mismatch_reason += f" (avg temp {day['avg_temp']}°F too cool for your {temp_preference} preference)"
                    elif temp_preference == "cool" and day["avg_temp"] >= 75.0:
                        matches_preferences = False
                        mismatch_reason += f" (avg temp {day['avg_temp']}°F too warm for your {temp_preference} preference)"
                    # Check if the day's weather condition matches the preference
                    if weather_condition_preference:
                        condition_mappings = {
                            "sunny": ["sunny", "clear"],
                            "cloudy": ["cloudy", "overcast"],
                            "rainy": ["rain", "shower", "drizzle"],
                            "clear": ["clear", "sunny"]
                        }
                        condition_matches = condition_mappings.get(weather_condition_preference.lower(), [weather_condition_preference.lower()])
                        if not any(condition in day["description"].lower() for condition in condition_matches):
                            matches_preferences = False
                            mismatch_reason += f" (not {weather_condition_preference})"
                    response += f"- {day['date']}: Avg {day['avg_temp']}°F (High {day['high_temp']}°F, Low {day['low_temp']}°F), {day['description']}{mismatch_reason}\n"
                    if matches_preferences:
                        response += f"  **This day matches your preferences for {temp_preference} and {weather_condition_preference} weather!**\n"
            response += "\nWould you like a forecast for another city or more details?"
            return response.strip()

        # Handle current weather queries (as before)
        if "weather" in query.lower() or "find" in query.lower():
            matching_cities = []
            non_matching_cities = []
            for city in preferred_cities:
                weather = get_current_weather(city)
                if "error" in weather:
                    continue
                matches_conditions = True
                mismatch_reason = ""
                # Check temperature preference
                if temp_preference == "warm" and weather["temp"] < 75.0:
                    matches_conditions = False
                    mismatch_reason += f" (too cool for your {temp_preference} preference)"
                elif temp_preference == "cool" and weather["temp"] >= 75.0:
                    matches_conditions = False
                    mismatch_reason += f" (too warm for your {temp_preference} preference)"
                # Check weather condition preference with mapping
                if weather_condition_preference:
                    condition_mappings = {
                        "sunny": ["sunny", "clear"],
                        "cloudy": ["cloudy", "overcast"],
                        "rainy": ["rain", "shower", "drizzle"],
                        "clear": ["clear", "sunny"]
                    }
                    condition_matches = condition_mappings.get(weather_condition_preference.lower(), [weather_condition_preference.lower()])
                    if not any(condition in weather["description"].lower() for condition in condition_matches):
                        matches_conditions = False
                        mismatch_reason += f" (not {weather_condition_preference})"
                if matches_conditions:
                    matching_cities.append(weather)
                else:
                    non_matching_cities.append(weather)

            # Report matching cities first
            if matching_cities:
                response += "Based on your preferences, here are some matching cities:\n"
                for city_weather in matching_cities:
                    response += f"- {city_weather['city']}: {city_weather['temp']}°F, {city_weather['description']}\n"

            # Always report weather for preferred cities, even if they don't match
            if preferred_cities:
                response += "Here’s the current weather in your preferred cities:\n"
                for city_weather in (matching_cities + non_matching_cities):
                    mismatch_reason = ""
                    if city_weather not in matching_cities:
                        if temp_preference == "warm" and city_weather["temp"] < 75.0:
                            mismatch_reason += f" (too cool for your {temp_preference} preference)"
                        elif temp_preference == "cool" and city_weather["temp"] >= 75.0:
                            mismatch_reason += f" (too warm for your {temp_preference} preference)"
                        if weather_condition_preference and not any(condition in city_weather["description"].lower() for condition in condition_mappings.get(weather_condition_preference.lower(), [weather_condition_preference.lower()])):
                            mismatch_reason += f" (not {weather_condition_preference})"
                    response += f"- {city_weather['city']}: {city_weather['temp']}°F, {city_weather['description']}{mismatch_reason}\n"
            else:
                response += "You haven't set any preferred cities yet. Would you like to add one, like 'I like Tucson'?\n"

            response += "Would you like to check the weather in another city or update your preferences?"

    # If query isn't weather-related, list preferences
    if not response:
        response = "Here are your preferences:\n"
        if preferred_cities:
            response += f"- Preferred cities: {', '.join(preferred_cities)}\n"
        if temp_preference:
            response += f"- Temperature preference: {temp_preference} weather\n"
        if weather_condition_preference:
            response += f"- Weather condition preference: {weather_condition_preference}\n"

    return response.strip()

get_preferences_tool = Tool(
    name="get_user_preferences",
    func=get_user_preferences,
    description="Retrieves the user's stored preferences and proactively provides weather updates or forecasts for preferred cities, noting if they match temperature and weather condition preferences. Handles forecast queries for preferred cities. Input examples: 'What are my preferences?', 'What's the weather like?', 'What's the forecast for my preferred cities?'."
)

# Initialize Grok 3 API with LangChain
llm = ChatXAI(api_key=GROK3_API_KEY, model="grok-3-mini")

# Create a conversational prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a weather assistant for nomads. Use the tools to answer weather-related queries conversationally. For historical weather, provide the average highs and lows in a clear, friendly format. For weather forecasts, include the daily average temperature, high, low, and most frequent weather condition in a detailed, friendly response. Use the get_user_preferences tool to check user preferences when relevant (e.g., for queries like 'What's the weather in my preferred cities?', check preferred cities and apply preferences). For direct single-city weather queries (e.g., 'What's the weather in Knoxville?'), use weather_lookup directly without checking preferences unless explicitly asked. You can also store user preferences like preferred cities or temperature preferences using the update_user_preferences tool. For combined queries, break them down into separate tool calls: e.g., for 'What's the weather in Knoxville today, and what's the forecast for the next few days?', first use weather_lookup to get current weather, then use forecast_weather to get the forecast. For comparison queries (e.g., 'Compare the weather in Knoxville and Tucson this week'), invoke forecast_weather for each city separately (e.g., call forecast_weather for Knoxville, then for Tucson), and summarize the results. If a query involves both current weather and forecast, split it into two steps: use weather_lookup for 'today' and forecast_weather for future days. Always provide clear, actionable responses tailored for nomads on the move. If a query requires multiple steps, execute them sequentially and summarize the findings in a single response. If a query is preprocessed into simpler parts (e.g., 'What's the forecast for Knoxville?' and 'What's the forecast for Tucson?'), handle each part directly without attempting to combine tools like 'forecast_weatherforecast_weather'."),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

# Preprocess queries to handle combined queries explicitly
def preprocess_query(query):
    # Handle "today and forecast" queries
    if "today" in query.lower() and "forecast" in query.lower():
        # Split into two queries
        try:
            city = query.lower().split("in ")[1].split(" today")[0].strip()
            return {"type": "today_and_forecast", "city": city, "queries": [
                f"What's the weather in {city}?",
                f"What's the forecast for {city}?"
            ]}
        except IndexError:
            return {"type": "single", "queries": [query]}
    # Handle comparison queries
    if "compare" in query.lower() and "and" in query.lower():
        # Extract cities
        try:
            parts = query.lower().split("in ")[1].split(" this week")[0]
            cities = [city.strip() for city in parts.split(" and ")]
            return {"type": "comparison", "cities": cities, "queries": [
                f"What's the forecast for {city}?" for city in cities
            ]}
        except IndexError:
            return {"type": "single", "queries": [query]}
    # Default: return original query as a single-item list
    return {"type": "single", "queries": [query]}

# Wrap the agent executor to handle preprocessed queries
class PreprocessedAgentExecutor:
    def __init__(self, executor):
        self.executor = executor

    def invoke(self, input_dict):
        query = input_dict["input"]
        preprocessed = preprocess_query(query)
        queries = preprocessed["queries"]
        responses = []
        for q in queries:
            response = self.executor.invoke({"input": q})
            responses.append(response["output"])
        # Combine responses into a single output
        if preprocessed["type"] == "today_and_forecast":
            city = preprocessed["city"]
            return {"output": f"Let’s break this down for {city.capitalize()}!\n\n**Today’s Weather:**\n{responses[0]}\n\n**Forecast for the Next Few Days:**\n{responses[1]}"}
        elif preprocessed["type"] == "comparison":
            cities = preprocessed["cities"]
            return {"output": f"Here's a comparison of the weather in {cities[0].capitalize()} and {cities[1].capitalize()}:\n\n**{cities[0].capitalize()} Forecast:**\n{responses[0]}\n\n**{cities[1].capitalize()} Forecast:**\n{responses[1]}"}
        return {"output": responses[0]}

# Create the agent with tools
tools = [weather_tool, warm_places_tool, historical_weather_tool, forecast_weather_tool, update_preferences_tool, get_preferences_tool]
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
base_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=20)
agent_executor = PreprocessedAgentExecutor(base_executor)

# Test the conversational agent with end-to-end diverse queries
queries = [
    # Reset preferences for a clean test
    "I like Knoxville",
    "I like Tucson",
    "I like sunny weather",
    "I prefer warm weather",
    # Current weather queries
    "What's the weather in Knoxville?",
    "What's the weather in my preferred cities?",
    # Historical weather queries
    "What were the average highs and lows in Knoxville in June?",
    "What were the average highs and lows in Tucson in December?",
    # Forecast weather queries
    "What's the forecast for Knoxville?",
    "What's the forecast for my preferred cities?",
    # Combined queries
    "What's the weather in Knoxville today, and what's the forecast for the next few days?",
    "Compare the weather in Knoxville and Tucson this week.",
    # Edge cases
    "What's the forecast for InvalidCity?",
    "I like InvalidCity",
    # Preference management
    "What are my preferences?"
]

for query in queries:
    print(f"\nQuery: {query}")
    response = agent_executor.invoke({"input": query})
    print(f"Response: {response['output']}")