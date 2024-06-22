from commands.xrpl.xrplCommands import XRPClient

from interactions import Intents, Client, listen, slash_command, slash_attachment_option, slash_str_option, InteractionContext
from interactions import Button, ButtonStyle, Embed # Confirmation Imports
from interactions.api.events import Component

from aiohttp import ClientSession
from io import StringIO
from csv import reader as csvReader
from asyncio import TimeoutError

intents = Intents.DEFAULT | Intents.MESSAGE_CONTENT
client = Client(intents=intents, token="MTI1MzIwMzA4ODI5MDg3MzM0NQ.GwFoBh.yYaVn7PYcnk-ZQbw3rUG0FyGwklBV-IlwAYeT8") # Transfer this to the 

xrplInstance = XRPClient(testMode=True, verbose=True)

@listen()
async def on_ready():
    
    print("Discord Bot Ready!")

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
    await ctx.defer()
        
    csvfile = ""

    if ctx.kwargs['csv_file'].filename.split(".")[-1] != 'csv':
        await statusMessage.edit(content=f"{statusMessage.content}\nError: Make sure that the file ends with .csv")
        return
    else:
        async with ClientSession() as session:
            async with session.get(ctx.kwargs['csv_file'].url) as response:
                csvfile = await response.text()
         
    recipientAddresses = list(csvReader(StringIO(csvfile)))
    
    if ctx.kwargs['seed_phrase'] is None:
        await statusMessage.edit(content=f"{statusMessage.content}\nSeed Phrase of the sender is required for the airdrop")
    else:
        await xrplInstance.registerSeed(ctx.kwargs['seed_phrase'])
     
    if "currency" in ctx.kwargs.keys():
        currency = ctx.kwargs['currency']
    else:
        currency = "XRP"
        
    if "memo" in ctx.kwargs.keys():
        memos = ctx.kwargs['memo']
    else:
        memos = None

    # Confirm the details of the airdrop
    recipientNum = len(recipientAddresses)
    statusMessage = await ctx.send(
        f"**Please confirm the details of the airdrop:**\n"
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

    def check(buttonCTX: Component):
        return buttonCTX.ctx.author.id == ctx.author.id and buttonCTX.ctx.custom_id in ["confirm", "cancel"]

    try:
        buttonCTX: Component = await client.wait_for_component(components=statusMessage.components, check=check, timeout=60.0)
        await statusMessage.suppress_embeds()
        if buttonCTX.ctx.custom_id == "cancel":
            await statusMessage.edit(content=f"{statusMessage.content}\n\nAirdrop cancelled.", components=[], embed = None)
            return
        await statusMessage.edit(content=f"{statusMessage.content}\n\nAirdrop confirmed.\n\nProcessing...\n\n", components=[], embed = None)
    except TimeoutError:
        await statusMessage.edit(content=f"{statusMessage.content}\n\nAirdrop cancelled due to timeout.", components=[], embed = None)
        return

    await statusMessage.edit(content=f"{statusMessage.content}\nStarting to send to {len(recipientAddresses)} addresses\n")
    successSend = 0
    errorCount = 0
    baseMessage = statusMessage.content
    for row in recipientAddresses:
        address, value = row
        try:
            result = await xrplInstance.sendCoin(address = address, value = value, coinHex = currency, memos = memos)
            if result['result']:
                successSend += 1
                # Message to send that the coin was successfully sent
                await statusMessage.edit(content=f"{baseMessage}\nSuccess: {successSend}/{recipientNum}")
            else:
                if errorCount < 5:
                    await statusMessage.edit(content=f"{baseMessage}\n**{result['error'] if result['error'] else "Unknown"}** error sending to {address}\n")
                    baseMessage = statusMessage.content
                errorCount += 1
        except Exception as e:
            continue
    
    await statusMessage.edit(content=f"{baseMessage}\n\n{successSend}/{recipientNum} Airdrop Complete!")

client.start()