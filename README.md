# ChestShop Market Analysis Bot for Discord

## Description

This tool specializes in parsing and analyzing market transaction logs from the ChestShop plugin used in Minecraft servers. It provides a comprehensive overview of market activities, enabling users to gain insights into the economic dynamics of the Minecraft world. The tool can be extremely useful for server admins, players, and Minecraft economists alike, offering a detailed look into player transactions, item pricing, and market trends.

The ChestShop Analyzer in this repo presents two integrations:

- **Streamlit Integration**: Utilizes Streamlit to create a dynamic, user-friendly web interface. This dashboard allows users to visualize the data through interactive charts and graphs, in an organised and orderly manner. The logs are parsed through `logs-parser.py` and automatically inserted into a SQLite Database, which is then read and analysed in the Streamlit Interface.
- **Discord Bot**: The Discord bot version allows players to gain insights on the data directly on Discord, allowing its integration into official Minecraft Discord servers, fostering a collaborative environment for economic and gameplay discussions. Users can interact with the bot using commands to retrieve specific market data, such as current item prices, player transaction history, and overall market trends.

## Getting Started

Follow these steps to set up the ChestShop Analyzer on your server:

1. **ChestShop Parsing**:
   - Create a /logs directory.
   - Upload your logs into the folder.
   - Navigate to the main directory
   - Run `python logs-parser.py`
2. **Streamlit Setup**:
   - Ensure you have Python and Streamlit installed.
   - Navigate to the Streamlit directory in the cloned repo.
   - Run `streamlit run app.py` to start the web dashboard.

3. **Discord Bot Setup**:
   - Set up your Discord bot token as described in the Configuration section.
   - Run `python discord_bot.py` to start the Discord bot.
   - Use the bot commands within your Discord server to interact with the ChestShop Analyzer.

  
In its current state, the bot is perfectly functioning, but the code is highly unoptimised. To address this, I'm planning a future comprehensive revision.

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Ancastal/ChestShop-Analyzer
cd ChestShop-Analyzer
pip install -r requirements.txt
```

## Discord Usage
Users can interact with the bot through various commands within Discord:

- `!price <item>`: Shows median and average prices for an item.
- `!history <item>`: Displays the price history of a particular item.
- `!inspect <item> [month]`: Shows the trade volume for an item.
- `!player <player_name>`: Retrieves market transactions associated with a specific player.
- `!tax <month>`: Reports the accumulated ChestShop tax for a specified month.
- and many more...

## License
This project is licensed under MIT License. See LICENSE.md for more details.

