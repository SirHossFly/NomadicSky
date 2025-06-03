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
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, return default structure
        return {"preferred_cities": [], "temperature_preference": None}

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
    description="Updates user preferences, such as preferred cities, temperature preferences, or weather conditions. Input examples: 'I like Knoxville', 'I like sunny weather', 'I prefer warm weather'."
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
    if preferred_cities and ("weather" in query.lower() or "find" in query.lower()):
        # Check weather in preferred cities
        matching_cities = []
        non_matching_cities = []
        for city in preferred_cities:
            weather = get_current_weather(city)
            if "error" in weather:
                continue
            matches_conditions = True
            
            # Check temperature preference
            if temp_preference == "warm" and weather["temp"] < 75.0:
                matches_conditions = False
            elif temp_preference == "cool" and weather["temp"] >= 75.0:
                matches_conditions = False

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
    description="Retrieves the user's stored preferences and proactively provides weather updates for preferred cities, noting if they match temperature and weather condition preferences. Input examples: 'What are my preferences?', 'What's the weather like?', 'Find warm places'."
)

# Initialize Grok 3 API with LangChain
llm = ChatXAI(api_key=GROK3_API_KEY, model="grok-3-mini")

# Create a conversational prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a weather assistant for nomads. Use the tools to answer weather-related queries conversationally. For historical weather, provide the average highs and lows in a clear, friendly format. Use the get_user_preferences tool to check user preferences when relevant (e.g., for weather queries, check preferred cities; for finding warm places, consider temperature preferences). You can also store user preferences like preferred cities or temperature preferences using the update_user_preferences tool."),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

# Create the agent with tools
tools = [weather_tool, warm_places_tool, historical_weather_tool, update_preferences_tool, get_preferences_tool]
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Test the conversational agent with enhanced preference-aware queries
queries = [
    "I like Knoxville",
    "I like sunny weather",
    "I prefer warm weather",
    "What's the weather like?",
    "What are my preferences?"
]

for query in queries:
    print(f"\nQuery: {query}")
    response = agent_executor.invoke({"input": query})
    print(f"Response: {response['output']}")