# XRPL Discord Bot
A Discord bot designed to facilitate transactions on the XRP Ledger, including sending XRP and custom coins to specified addresses via a CSV file using a slash command in Discord. Developed using Python and Discord's Interaction module, with integration of the XRPL Python module.

## Features
Send XRP: Automatically send XRP to multiple addresses specified in a CSV file.
Send Custom Coins: Send custom coins on the XRP Ledger using trustlines for the 'issuer' parameter.
Slash Command Integration: Use Discord slash commands to trigger transactions.
CSV Integration: Import addresses and amounts from a CSV file for bulk transactions.
Technologies Used
Programming Language: Python
Discord Interaction Module: For creating and handling slash commands in Discord.
XRPL Python Module: For interacting with the XRP Ledger and performing transactions.

## Installation
1. Clone the Repository:<br>Copy code
  ```bash
git clone https://github.com/yourusername/xrpl-discord-bot.git
cd xrpl-discord-bot

  ```

2. Install Dependencies: <br> Copy code
```bash
pip install -r requirements.txt
```
3. Set Up Environment Variables:<br>
   Modify the ```config.ini``` in the root directory and add your Discord bot token.
```bash
nano config.ini
```
4. Run the Bot:
```bash
python bot.py
```

## Usage
1. Prepare CSV File:
* Create a CSV file with two columns: address and amount.
* Populate the file with the recipient addresses and the amounts to send.
  
2. Slash Command:
* Use the slash command /sendxrp followed by the path to your CSV file.
* Example: /sendxrp /path/to/your/recipients.csv
   
4. Send Custom Coins:
* Use the slash command /sendcustom followed by the path to your CSV file.
* Example: /sendcustom /path/to/your/recipients.csv

## Challenges and Solutions
### Integrating Custom Coin Transactions:
The main challenge was automatically setting the ```issuer``` parameter for custom coins.
### Solution:
Utilized trustlines to determine the issuer, allowing for seamless custom coin transactions.

## Future Enhancements
1. Enhanced Error Handling: Improve error messages and logging for better troubleshooting.
2. Transaction History: Add functionality to retrieve and display transaction history.
3. Balance Checking: Integrate commands to check balances of XRP and custom coins.
4. Multithreading: Implement multithreading to hasten the sending of transactions.

## Contributing
1. Fork the Repository:
   ..1. Click the "Fork" button at the top right of this repository's page.

3. Clone Your Fork:

``` bash
git clone https://github.com/angelmacm/xrpl-discord.git
cd xrpl-discord-bot
```

3. Create a Branch:
```bash
git checkout -b feature/your-feature-name
```

4. Make Your Changes:<br>Implement your feature or bug fix.
  
6. Commit Your Changes: <br>
```bash

git add .
git commit -m "Add feature/your-feature-name"
```

6. Push to Your Fork:
```bash
git push origin feature/your-feature-name
```

7. Create a Pull Request: <br>Navigate to your forked repository on GitHub and click the "New Pull Request" button.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For any questions or inquiries, please contact me at [angelmac_m@yahoo.com](mailto:angelmac_m@yahoo.com).
