NomadicSky Project Charter

Project Name
NomadicSky

Project Purpose
The NomadicSky project aims to develop a weather-focused AI agent to assist nomads, such as RV travelers, in planning safe and optimal travel. The agent will provide real-time weather data, historical weather insights, severe weather risk alerts, and local National Weather Service (NWS) office details, with personalized responses based on user preferences. As a personal learning project, it will enable mastery of LangChain, Grok 3 API, and GitHub Copilot through hands-on development.

Objectives
1.	Deliver a functional Minimum Viable Product (MVP) that supports nomads with weather-based travel planning.
2.	Provide local NWS office contact details (X handle, website link) to enhance safety and trust.
3.	Personalize responses using stored user preferences for a tailored nomad experience.
4.	Learn LangChain concepts (chains, tools, agents, memory), GitHub Copilot for AI-assisted coding, and project management practices over 3 weeks.
5.	Complete the project within a $100 budget, leveraging free APIs and cost-efficient tools.

Scope
In Scope (MVP Features)
1.	Current Weather Conditions:
o	Queries like "What's the weather in Knoxville, TN?"
o	Uses OpenWeatherMap API for real-time data (temperature, conditions, wind speed).
o	Nomad-friendly responses (e.g., "Knoxville: 75°F, partly cloudy, great for hiking").
2.	Historical Weather Insights:
o	Queries like "What's Knoxville like in spring?"
o	Uses NOAA API for seasonal averages; compares to user's stored data.
o	Responses like "Knoxville spring: 60-75°F, similar to your last visit."
3.	Severe Weather Risk Alerts:
o	Queries like "Is Texas safe in spring?"
o	Uses NOAA/OpenWeatherMap for risks (e.g., Texas spring tornadoes, Pacific coast winds, New England mud/rain).
o	Nomad advice like "Texas, March-May: high tornado risk, plan for shelters."
4.	User Preference Memory:
o	Stores preferences (e.g., "70-80°F, low risk areas").
o	Applies to responses (e.g., "Knoxville fits your preferences").
o	Handles multi-turn dialogues.
5.	Local NWS Office Details:
o	Provides X handle and website (e.g., Knoxville -> Morristown, TN, @NWSMorristown, www.weather.gov/mrx).
o	Uses static JSON file (10-20 nomad destinations, expandable in design phase).

Out of Scope
•	Campground recommendations, job search, cost estimation, amenities lookup, route planning.
•	Real-time severe weather alerts (use seasonal risks).
•	Automated location tracking (manual input).
•	Comprehensive NWS JSON (expand later).
•	Advanced UI (command-line/Jupyter interface).

Deliverables
•	Python scripts implementing the MVP, hosted in a GitHub repository (e.g., github.com/yourname/NomadicSky).
•	Command-line or Jupyter interface for user queries.
•	README documenting setup, usage, and features.
•	Static JSON file with NWS office details for 10-20 cities.

Timeline
Duration: 3 weeks
Effort: 10-15 hours total (~3.3-5 hours/week, within 10 hours/week availability)

Milestones:
•	Week 1 (3-4 hours):
o	Setup development environment (2-3 hours): Install Python, Miniconda, VSCode, GitHub Copilot, Git, Postman, Jupyter; configure GitHub repo, Grok 3 API, OpenWeatherMap/NOAA APIs; test basic script.
o	Current weather start (0-1 hour): Begin LangChain chain for OpenWeatherMap.
•	Week 2 (4-6 hours):
o	Current weather completion (1-2 hours): Finish OpenWeatherMap tool.
o	Historical weather + memory (3-4 hours): NOAA API, LangChain memory.
•	Week 3 (3-5 hours):
o	Severe weather + NWS details (2-3 hours): NOAA/OpenWeatherMap risks, JSON for NWS.
o	Testing, polish, README (1-2 hours): Debug, refine, document.
Budget
Total: $45-$85 (within $100)

Breakdown:
•	Grok 3 API: $5-$10 (50-100 queries/day, 1.25-2.5 million tokens, 80% Grok 3 Mini).
•	Other APIs: $0-$15 (OpenWeatherMap/NOAA free, optional Weather Underground/Nominatim $0-$15).
•	Tools: $40-$60 (GitHub Copilot $20 for 2 months, Udemy course $0-$20, cloud hosting $0-$10, existing tools $0). Buffer: $15-$55

Resources

Technology
•	Framework: LangChain (chains, tools, agents, memory).
•	LLM: Grok 3 API (80% Mini, 20% Grok 3).
•	APIs: OpenWeatherMap, NOAA, static JSON for NWS.
•	Tools: VSCode, GitHub, GitHub Copilot, Python/pip, Miniconda, Postman, Jupyter, Git CLI.

Learning
•	Hands-on training guided by Grok AI, using LangChain documentation, DeepLearning.AI/YouTube tutorials, GitHub Copilot for coding, and an optional Udemy course.

Stakeholders
•	Project Owner/Lead: Mark, responsible for coding, learning, and decision-making.
•	Mentor/Guide: Grok AI, providing personalized training, code examples, and project planning support.
•	Target Users: Nomads (e.g., RV travelers) seeking weather-focused travel planning.

Success Criteria
•	MVP successfully answers weather queries with current, historical, and risk data, including NWS details.
•	User preferences are stored and applied for personalized responses.
•	Project completed within 3 weeks, 10-15 hours, and $100 budget.
•	Mastery of LangChain, GitHub Copilot, and project management concepts through hands-on development.
•	Functional GitHub repository with clear documentation.

Risks and Mitigation
•	Risk: Limited NWS JSON coverage (10-20 cities).
o	Mitigation: Focus on popular nomad destinations; plan expansion in design phase.
•	Risk: API limitations (e.g., NOAA data complexity).
o	Mitigation: Use simple metrics; leverage Grok 3 for parsing.
•	Risk: Time constraints due to setup (non-configured laptop).
o	Mitigation: Allocate Week 1 for setup, use guided training.
•	Risk: Budget overrun.
o	Mitigation: Monitor Grok 3 usage, prioritize free APIs, use Copilot trial if available.

