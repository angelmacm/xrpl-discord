from commands.xrpl.xrplCommands import XRPClient

from interactions import Intents, Client, listen, InteractionContext # General discord Interactions import
from interactions import slash_command, slash_attachment_option, slash_str_option, slash_bool_option # Slash command imports
from interactions import Button, ButtonStyle, Embed # Confirmation Imports
from interactions.api.events import Component

# Other imports
from aiohttp import ClientSession
from io import StringIO
from csv import reader as csvReader
from asyncio import TimeoutError
from configparser import ConfigParser

config = ConfigParser()
config.read("../config.ini")
intents = Intents.DEFAULT | Intents.MESSAGE_CONTENT
client = Client(intents=intents, token=config['BOT']['token']) # Transfer this to the 

xrplInstance = XRPClient()

@listen()
async def on_ready():
    # Some function to do when the bot is ready
    print("Discord Bot Ready!")

# Airdrop Command:
# Parameters:
#       CSV File: [Required] .csv attachment consists of addresses and how many to send to them
#       Seed Phrase: [Required] sender's seed phrase to be used as a source of funds.
#       Currency: [Optional] Currency Code for the funds that would be transferred. If not set, default to XRP
#       Memo: [Optional] A quick message that would be transferred along with the payment
@slash_command(
        name="airdrop",
        description="Airdrop Coins to users",
        options= [
            slash_attachment_option(
                name = "csv_file",
                description = "List of addresses and the corresponding value of coins to be sent saved in a .csv",
                required = True
            ),
            slash_str_option(
                name = "seed_phrase",
                description = "Seed Phrase of the sender account",
                required = True
            ),
            slash_str_option(
                name = "currency",
                description = "Hex Code of the custom coin, leave it blank if XRP",
                required = False
            ),
            slash_str_option(
                name = "memo",
                description = "Memo for the transaction",
                required = False
            )
        ])
async def airdrop(ctx: InteractionContext):
    await ctx.defer() # Defer the response to wait for the function to run.
        
    csvfile = ""
    statusMessage = await ctx.send(content="Checking parameters...") # Give a quick status update
    
    # Start of parameter checking
    
    # Check the attachment if its suffix is .csv
    if ctx.kwargs['csv_file'].filename.split(".")[-1] != 'csv':
        await statusMessage.edit(content=f"{statusMessage.content}\nError: Make sure that the file ends with .csv")
        return
    else:
        # Download the contents of the attachment
        async with ClientSession() as session:
            async with session.get(ctx.kwargs['csv_file'].url) as response:
                csvfile = await response.text()
    
    # Parse the contents of the attachments
    recipientAddresses = list(csvReader(StringIO(csvfile)))
    
    # Check if the seed is valid and register it as the wallet
    seedResult = await xrplInstance.registerSeed(ctx.kwargs['seed_phrase'])
    if not seedResult['result']:
        await statusMessage.edit(content=f"{statusMessage.content}\n[{seedResult['error']}] error while registering wallet with seed: {ctx.kwargs['seed_phrase']}")
        return
        
    # Check if currency is given, else default to XRP
    if "currency" in ctx.kwargs.keys():
        currency = ctx.kwargs['currency']
    else:
        currency = "XRP"
    
    # Check if memo is given, ignore if not.
    if "memo" in ctx.kwargs.keys():
        memos = ctx.kwargs['memo']
    else:
        memos = None

    recipientNum = len(recipientAddresses)
    
    # Confirm the details of the airdrop
    statusMessage = await statusMessage.edit(content=
        f"**Please confirm the details of the airdrop:**\n"
        f"XRP Network: **{'Testnet' if xrplInstance.getTestMode() else 'Mainnet'}**\n"
        f"Currency: **{currency}**\n"
        f"Seed Phrase: **{ctx.kwargs['seed_phrase']}**\n\n"
        f"Number of recipients: **{recipientNum}**\n\n"
        f"**CSV File**\n"
        f"[{ctx.kwargs['csv_file'].filename}]({ctx.kwargs['csv_file'].url})"
        f"\n\nMemos: {memos if memos else ''}", # Conditional Rendering
        
        embed=Embed(title="Confirm Airdrop Information",
                    description="You have **60 Seconds** to confirm the details above. Failure to confirm will result in airdrop **__CANCELLATION__**"),                    
        
        components=[
                Button(style=ButtonStyle.GREEN, label="Confirm", custom_id="confirm"),
                Button(style=ButtonStyle.RED, label="Cancel", custom_id="cancel")
        ]
    )

    # Function to receive the value when the confirmatory buttons are pressed
    def check(buttonCTX: Component):
        return buttonCTX.ctx.author.id == ctx.author.id and buttonCTX.ctx.custom_id in ["confirm", "cancel"]

    try:
        # Send the Confirmation message and wait for 60s for answer
        buttonCTX: Component = await client.wait_for_component(components=statusMessage.components, check=check, timeout=60.0)
        
        # Remove the embeds then remove the components and reply according to what response the app got
        await statusMessage.suppress_embeds()
        if buttonCTX.ctx.custom_id == "cancel":
            await statusMessage.edit(content=f"{statusMessage.content}\n\nAirdrop cancelled.", components=[], embed = None)
            return
        await statusMessage.edit(content=f"{statusMessage.content}\n\nAirdrop confirmed.\n\nProcessing...\n\n", components=[], embed = None)
    except TimeoutError:
        await statusMessage.edit(content=f"{statusMessage.content}\n\nAirdrop cancelled due to timeout.", components=[], embed = None)
        return

    # Give a quick status update
    await statusMessage.edit(content=f"{statusMessage.content}\nStarting to send to {len(recipientAddresses)} addresses\n")
    
    # Mini Statistics
    successSend = 0
    errorCount = 0
    
    # Save a base message to rerender the results
    baseMessage = statusMessage.content
    
    # loop through the addresses
    for row in recipientAddresses:
        
        # prevent parsing empty and incomplete indexes
        if len(row)>1:
            continue
        
        # Parse the current row then perform the XRPL transaction
        # TODO: Make these generate multiple thread for faster airdrop
        address, value = row
        try:
            result = await xrplInstance.sendCoin(address = address, value = value, coinHex = currency, memos = memos)
            if result['result']:
                successSend += 1
                # Message to send that the coin was successfully sent
                await statusMessage.edit(content=f"{baseMessage}\nSuccess: {successSend}/{recipientNum}")
            else:
                if errorCount < 5:
                    await statusMessage.edit(content=f"{baseMessage}\n**{result['error'] if result['error'] else 'Unknown'}** error sending to {address}\n")
                    baseMessage = statusMessage.content
                errorCount += 1
        except Exception as e:
            continue
    # Make a final confirmation message
    await statusMessage.edit(content=f"{baseMessage}\n\n{successSend}/{recipientNum} Airdrop Complete!")
    
# Network Command:
# Parameters: 
#   testmode: [Required] Boolean if the network should be configure to testnet    
@slash_command(
        name="network",
        description="Configure XRP network",
        options= [
            slash_bool_option(
                description="True or False if it should be configured to testnet",
                name="testmode",
                required=True
            )
            ])
async def setTestMode(ctx: InteractionContext):
    await ctx.defer() # Defer the response to wait for the function to run.
    
    # Parse the argument and set it to the XRPL Instance
    testMode = ctx.kwargs['testmode']
    xrplInstance.setTestMode(testMode)
    
    # Check if the XRPL Instace successfully set the correct mode and send the result to the chat
    if xrplInstance.getTestMode() == testMode:
        await ctx.send(content=f"Bot configure to XRP {'Testnet' if testMode else 'Mainnet'}")
    else:
        await ctx.send(content=f"Unknown error tring to set testMode={testMode}")
        
if __name__ == "__main__":
    client.start()