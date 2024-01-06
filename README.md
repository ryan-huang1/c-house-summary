## Overview
Detects "/summary", sends all messages after the message the /summary message replys to, to be summarized

Digital Ocean droplet hosting signal-cli-rest-api -> replit hosted server calling that for updates -> storing all messages from this group chat + checking for a /summary message -> send those message to OAI when /summary is triggered -> calling the signal-cli-rest-api to send the summary

### Server Setup: `signal-cli-rest-api`
Before running this application, you need to set up the `signal-cli-rest-api` server. This server acts as an intermediary, handling Signal messaging operations. This is the server that the application calls on

**Set Environment Variables**:
   - Set the following environment variables for API keys and server URLs:
     - `OPENAI_API_KEY`: Your OpenAI API key.
     - `SERVER_URL_SEND`: URL to send messages.
     - `SERVER_URL_RECEIVE`: URL to receive messages.
     - `SERVER_USERNAME`: Username for server authentication.
     - `SERVER_PASSWORD`: Password for server authentication.
     - `GROUP_ID`: Group ID for filtering messages.
     - `USER_NUMBER`: Your number, the message will be sent from

## Contributing
- Contributions are welcome, please for the love of god someone make this code actully look pretty

## License
- Licensed under the ryan put two hours into this, use it however you want license.
