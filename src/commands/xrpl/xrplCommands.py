from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.wallet import Wallet
from xrpl.asyncio.account import get_balance
from xrpl.asyncio.transaction import autofill_and_sign, submit_and_wait
from xrpl.models.transactions import Payment, Memo
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops
from xrpl.models.requests.account_lines import AccountLines
from xrpl.models.requests import RipplePathFind
from asyncio import sleep
from configparser import ConfigParser

class XRPClient:
    def __init__(self, verbose=False) -> None:
        self.config = ConfigParser()
        self.config.read("../config.ini")
        self.setTestMode(self.config.getboolean("XRPL",'test_mode'))
        self.lastCoinChecked = ""
        self.lastCoinIssuer = ""
        self.verbose = verbose

    async def sendCoin(self, address: str, value: float, coinHex: str = "XRP", memos: str | None = None) -> dict:
        print() if self.verbose else None
        funcResult = {'result': False, 'error': None}
        if memos:
            memoData = memos.encode('utf-8').hex()
        
        print("Preparing payment package...") if self.verbose else None
        try:
            if coinHex.upper() == "XRP":
                amount_drops = xrp_to_drops(float(value))
                payment = Payment(
                    account=self.wallet.classic_address,
                    destination=address,
                    amount=amount_drops,
                    memos= [Memo(memo_data=memoData)] if memos else None
                )
            else:
                coinIssuer = await self.getCoinIssuer(coinHex)
                
                if coinIssuer is None:
                    funcResult["error"] = "TrustlineNotSet"
                    funcResult["result"] = False
                    return funcResult
                
                payment = Payment(
                    account=self.wallet.classic_address,
                    destination=address,
                    amount={
                        "currency": coinHex,
                        "value": str(value),  # Ensure amount is a string
                        "issuer": coinIssuer
                    },
                    memos= [Memo(memo_data=memoData)] if memos else None
                )
            
            # Retry logic with delay between retries
            retries = 3
            for attempt in range(retries):
                print(f"Attempt #{attempt+1} in sending {value} {coinHex} to {address}") if self.verbose else None
                try:
                    async with AsyncWebsocketClient(self.xrpLink) as client:
                        # Sign the transaction
                        signed_tx = await autofill_and_sign(transaction=payment, wallet=self.wallet, client=client)
                        
                        # Submit the signed transaction
                        result = await submit_and_wait(transaction=signed_tx, client=client)
                    
                    if result.is_successful():
                        funcResult["result"] = True
                        return funcResult
                    else:
                        raise Exception(result.result)
                except Exception as e:
                    
                    if "noCurrent" in str(e) or "overloaded" in str(e):
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying...") if self.verbose else None
                        await sleep(5)  # Wait before retrying
                    else:
                        raise e
            return False
        
        except Exception as e:
            print(f"Error processing {value} {coinHex} for {address}: {str(e)}") if self.verbose else None
            funcResult['result'] = False
            funcResult['error'] = e
            return funcResult
    
    async def pathFindAccounts(self, issuer, destination, value, currency):
        
        coinIssuer = await self.getCoinIssuer(currency)
        
        # Prepare RipplePathFind request
        path_find_request = RipplePathFind(
            source_account=issuer,
            destination_account=destination,
            destination_amount=IssuedCurrencyAmount(
                currency=currency,
                value=str(value),
                issuer=coinIssuer
            )
        )

        # Send the path find request
        async with AsyncWebsocketClient(self.xrpLink) as client:
            pathResponse = await client.request(path_find_request)
        
        if "alternatives" in pathResponse.result and len(pathResponse.result["alternatives"]) > 0:
            paths = pathResponse.result["alternatives"][0]["paths_computed"]
        else:
            raise Exception("Path Not Found")
        return paths
    
    async def getCoinIssuer(self, currency: str) -> str | None:
        
        # To prevent multiple request of the same coin
        if currency == self.lastCoinChecked:
            return self.lastCoinIssuer
        
        try:
            account_lines = AccountLines(
                account=self.wallet.classic_address,
                ledger_index="validated"
            )
            
            async with AsyncWebsocketClient(self.xrpLink) as client:
                response = await client.request(account_lines)

            if "lines" not in response.result.keys():
                return
            
            lines = response.result["lines"]
            for line in lines:
                
                if line["currency"] == currency:
                    self.lastCoinIssuer = line["account"]
                    return self.lastCoinIssuer
            return
        except Exception as e:
            print(f"Error checking trust line for {self.wallet.classic_address}: {str(e)}")
            return 
        
    async def checkBalance(self):
        async with AsyncWebsocketClient(self.xrpLink) as client:
            return await get_balance(self.wallet.address, client)
    
    def setTestMode(self, mode = True) -> None:
        if mode:
            self.xrpLink = self.config["XRPL"]["testnet_link"]
        else:
            self.xrpLink = self.config["XRPL"]["mainnet_link"]
        
    async def registerSeed(self, seed) -> dict:
        try:
            print("Registering Wallet...") if self.verbose else None
            self.wallet = Wallet.from_seed(seed)
            return {"result":True, "error": "success"}
        except Exception as e:
            print(f"Error in wallet registration") if self.verbose else None
            return {"result":False, "error":e}
    
    def getTestMode(self) -> bool:
        return self.xrpLink == self.config["XRPL"]["testnet_link"]