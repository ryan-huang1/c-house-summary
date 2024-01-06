## Overview
This Python application processes and summarizes text messages, utilizing Flask, SQLAlchemy, and OpenAI's GPT-4. It functions as a client to a Signal Messenger REST API server, specifically using `signal-cli-rest-api` to handle Signal messaging functionalities.

## Server Setup: `signal-cli-rest-api`
Before running this application, you need to set up the `signal-cli-rest-api` server. This server acts as an intermediary, handling Signal messaging operations.

### Steps to Setup `signal-cli-rest-api`
1. **Create Configuration Directory**:
mkdir $HOME/.local/share/signal-cli

This directory stores the Signal configuration, allowing container updates without re-registering your Signal number.

2. **Start Docker Container**:
sudo docker run -d --name signal-api --restart=always -p 8080:8080
-v $HOME/.local/share/signal-cli:/home/.local/share/signal-cli
-e 'MODE=native' bbernhard/signal-cli-rest-api

This command starts the `signal-cli-rest-api` in a Docker container.

3. **Register or Link Signal Number**:
Open `http://localhost:8080/v1/qrcodelink?device_name=signal-api` in a browser. Then, in your Signal mobile app, go to Settings > Linked Devices and scan the QR code.

4. **Test REST API**:
curl -X POST -H "Content-Type: application/json" 'http://localhost:8080/v2/send'
-d '{"message": "Test via Signal API!", "number": "+4412345", "recipients": ["+44987654"]}'

Replace `+4412345` with your Signal number and `+44987654` with the recipient's number.

## Contributing
- Contributions are welcome, please for the love of god someone make this code actully look pretty

## License
- Licensed under the ryan put two hours into this, use it however you want license.
