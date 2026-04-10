import sys
import os
import asyncio
from deriv_api import DerivAPI, APIError

# Parameters
APP_ID = 63411
API_TOKEN = os.getenv('DERIV_TOKEN', 'API TOKEN HERE')
DESIRED_STAKE = 10  # Desired stake amount in USD
MULTIPLIER = 100   # Multiplier value (up to 2000x)
TAKE_PROFIT = 50   # Close trade automatically at $50 profit
STOP_LOSS = 9.70     # Close trade automatically at $10 loss
SYMBOL = "R_100"   # Volatility 100 Index
PREDICTION = "up"  # "up" or "down"

if not API_TOKEN:
    sys.exit("DERIV_TOKEN environment variable is not set")

async def trading_bot():
    api = DerivAPI(app_id=APP_ID)
    await api.authorize(API_TOKEN)

    # Get initial balance
    balance = await api.balance()
    initial_balance = balance['balance']['balance']
    
    print(f"Starting Multipliers Trading")
    print(f"Initial Balance: ${initial_balance:.2f}")
    print(f"Desired Stake: ${DESIRED_STAKE}")
    print(f"Multiplier: {MULTIPLIER}x")
    print(f"Take Profit: ${TAKE_PROFIT}")
    print(f"Stop Loss: ${STOP_LOSS}")
    print(f"Symbol: {SYMBOL}")
    print("=" * 50)

    try:
        # Get proposal for multiplier contract
        contract_type = "MULTUP" if PREDICTION == "up" else "MULTDOWN"
        
        # First, try to get a proposal to see the maximum allowed stake
        proposal = await api.proposal({
            "proposal": 1,
            "amount": DESIRED_STAKE,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "symbol": SYMBOL,
            "multiplier": MULTIPLIER,
            "limit_order": {
                "take_profit": TAKE_PROFIT,
                "stop_loss": STOP_LOSS
            }
        })
        
        proposal_id = proposal.get('proposal', {}).get('id')
        if not proposal_id:
            print("Failed to get proposal")
            return
            
        proposal_data = proposal.get('proposal', {})
        
        # Check the actual stake that will be used
        actual_stake = proposal_data.get('ask_price', DESIRED_STAKE)
        
        print(f"\nProposal ID: {proposal_id}")
        print(f"Actual Stake: ${actual_stake:.2f}")
        print(f"Entry Spot: {proposal_data.get('entry_spot')}")
        print(f"Take Profit: ${proposal_data.get('limit_order', {}).get('take_profit')}")
        print(f"Stop Loss: ${proposal_data.get('limit_order', {}).get('stop_loss')}")
        print(f"Potential Payout: ${proposal_data.get('payout', 0):.2f}")
        
        # Confirm before placing trade
        print(f"\n⚠️  Maximum risk: ${actual_stake:.2f}")
        print(f"Maximum potential profit: ${(proposal_data.get('payout', 0) - actual_stake):.2f}")
        
        confirm = input("Place this trade? (y/n): ")
        if confirm.lower() != 'y':
            print("Trade cancelled")
            return
        
        # Place the trade
        buy_response = await api.buy({"buy": proposal_id, "price": actual_stake})
        contract_id = buy_response.get('buy', {}).get('contract_id')
        
        if not contract_id:
            print("Failed to buy contract")
            return
            
        print(f"\n✅ Trade Executed!")
        print(f"Contract ID: {contract_id}")
        print("Trade is now active. It will close automatically when:")
        print(f"  - Take Profit (${TAKE_PROFIT}) is reached")
        print(f"  - Stop Loss (${STOP_LOSS}) is reached")
        print(f"  - Stop-out level is reached (loss = stake)")
        print("  - Or you close it manually")
        
        # Monitor the contract
        while True:
            await asyncio.sleep(2)
            
            contract_details = await api.proposal_open_contract({
                "proposal_open_contract": 1,
                "contract_id": contract_id
            })
            
            if contract_details and 'proposal_open_contract' in contract_details:
                contract_info = contract_details['proposal_open_contract']
                status = contract_info.get('status')
                profit = contract_info.get('profit', 0)
                current_spot = contract_info.get('current_spot', 'N/A')
                
                print(f"Status: {status} | Current Spot: {current_spot} | P&L: ${profit:+.2f}")
                
                # Exit loop if contract is sold or expired
                if status in ['sold', 'expired']:
                    if profit > 0:
                        print(f"\n🎉 Trade closed with profit: ${profit:+.2f}")
                    else:
                        print(f"\n📉 Trade closed with loss: ${profit:+.2f}")
                    break
        
        # Final balance
        final_balance = await api.balance()
        final_amount = final_balance['balance']['balance']
        total_pnl = final_amount - initial_balance
        
        print("\n" + "=" * 50)
        print("TRADE COMPLETED")
        print("=" * 50)
        print(f"Initial Balance: ${initial_balance:.2f}")
        print(f"Final Balance: ${final_amount:.2f}")
        print(f"Total P&L: ${total_pnl:+.2f}")
        print(f"ROI: {(total_pnl/initial_balance*100):+.2f}%")
        
    except APIError as e:
        print(f"API Error: {e}")
        
        # If error is about amount too high, try to find maximum allowed
        if "Enter an amount equal to or lower than" in str(e):
            try:
                max_allowed = float(str(e).split("than ")[1].split(".")[0])
                print(f"\n💡 Maximum allowed stake is ${max_allowed:.2f}")
                print(f"Try running again with STAKE = {max_allowed:.2f}")
            except:
                print("\n💡 Try reducing your STAKE value")

if __name__ == "__main__":
    asyncio.run(trading_bot())