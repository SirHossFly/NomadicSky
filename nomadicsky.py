import requests
from langchain.tools import Tool
from langchain_xai import ChatXAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate

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

# Initialize Grok 3 API with LangChain
llm = ChatXAI(api_key=GROK3_API_KEY, model="grok-3-mini")

# Create a conversational prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a weather assistant for nomads. Use the tools to answer weather-related queries conversationally. For historical weather, provide the average highs and lows in a clear, friendly format."),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

# Create the agent with tools
tools = [weather_tool, warm_places_tool, historical_weather_tool]
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Test the conversational agent with historical weather queries
queries = [
    "What were the average highs and lows in Knoxville in June?",
    "Tell me about historical weather in Tucson for December."
]

for query in queries:
    print(f"\nQuery: {query}")
    response = agent_executor.invoke({"input": query})
    print(f"Response: {response['output']}")