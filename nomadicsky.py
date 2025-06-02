import requests
from langchain.tools import Tool

# Load OpenWeatherMap API key from api_keys.txt
def load_api_key():
    with open("api_keys.txt", "r") as file:
        for line in file:
            if line.startswith("OPENWEATHERMAP_API_KEY"):
                return line.split("=")[1].strip()
    raise ValueError("OPENWEATHERMAP_API_KEY not found in api_keys.txt")

OPENWEATHERMAP_API_KEY = load_api_key()

# Function to fetch current weather from OpenWeatherMap
def get_current_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=imperial"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        return f"{city}: {temp}°F, {description}"
    else:
        return f"Error fetching weather for {city}: {response.status_code}"

# Create a LangChain Tool for weather lookup
weather_tool = Tool(
    name="weather_lookup",
    func=get_current_weather,
    description="Fetches current weather for a given city."
)

# Test the tool directly
# Test the tool with multiple cities
cities = ["Tucson,AZ,US", "Austin,TX,US", "Portland,OR,US"]
for city in cities:
    print(weather_tool.run(city))