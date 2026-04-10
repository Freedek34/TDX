import sys
import os
import json
import random
import asyncio
import websockets
from deriv_api import ( DerivAPI, APIError,)

# Parameters# Parameters
APP_ID = 63411
API_TOKEN = os.getenv('DERIV_TOKEN','API TOKEN HERE')
BET_AMOUNT = 10
TOTAL_ROUNDS = 10
MARTINGALE_ENABLED = True  # Set to False to disable Martingale
MAX_MARTINGALE_STEPS = 5   # Maximum number of consecutive Martingale steps
MARTINGALE_MULTIPLIER = 2  # Bet multiplier after each loss
URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"

if not API_TOKEN:
    sys.exit("DERIV_TOKEN environment variable is not set")

async def collect_data():
    async with websockets.connect(URL) as websocket:
        await websocket.send(json.dumps({
            "ticks_history": "R_100",
            "adjust_start_time": 1,
            "count": 30,
            "end": "latest",
            "start": 1,
            "style": "ticks"
        }))
        response = await websocket.recv()
        data = json.loads(response)
        if 'history' in data and 'prices' in data['history']:
            prices = data['history']['prices']
            digits = [int(str(price)[-1]) for price in prices] 
            return digits
        else:
            print("Failed to retrieve data")
            return None

async def trading_bot():
    api = DerivAPI(app_id=APP_ID)
    await api.authorize(API_TOKEN)

    balance = await api.balance()
    initial_balance = balance['balance']['balance']
    current_bet_amount = BET_AMOUNT
    martingale_step = 0  # Track current Martingale step
    consecutive_losses = 0  # Track consecutive losses
    wins = 0
    losses = 0
    
    print(f"Starting trading session with initial balance: ${initial_balance}")
    print(f"Martingale {'ENABLED' if MARTINGALE_ENABLED else 'DISABLED'}")
    print(f"Max Martingale Steps: {MAX_MARTINGALE_STEPS}")
    print(f"Martingale Multiplier: {MARTINGALE_MULTIPLIER}x")
    print("=" * 50)

    for round_num in range(1, TOTAL_ROUNDS + 1):
        await asyncio.sleep(1)
        
        # Predict even or odd by simply randomizing it for now (UNCHANGED)
        predicted_even_odd = random.randint(0, 1)
        print(f"Predicted even/odd: {'Even' if predicted_even_odd == 1 else 'Odd'}")

        # Define contract type based on prediction (UNCHANGED)
        contract_type = "DIGITEVEN" if predicted_even_odd == 1 else "DIGITODD"

        print(f"Round {round_num}: Placing {contract_type} trade with bet amount ${current_bet_amount}")
        print(f"Martingale step: {martingale_step}/{MAX_MARTINGALE_STEPS}")

        try:
            # Get proposal for trade (ALL PARAMETERS INTACT)
            proposal = await api.proposal({
                "proposal": 1,
                "amount": float(max(current_bet_amount, 0.35)),
                "barrier": "0",  # KEPT AS IN ORIGINAL
                "basis": "stake",  # KEPT AS IN ORIGINAL
                "contract_type": contract_type,
                "currency": "USD",
                "duration": 1,
                "duration_unit": "t",
                "symbol": "R_100"
            })
            proposal_id = proposal.get('proposal', {}).get('id')
            if not proposal_id:
                print("Failed to get proposal")
                continue
        except APIError as e:
            print(f"Failed to get proposal: {e}")
            continue
        
        try:
            # Place trade (UNCHANGED)
            buy_response = await api.buy({"buy": proposal_id, "price": current_bet_amount})
            contract_id = buy_response.get('buy', {}).get('contract_id')
            if not contract_id:
                print("Failed to get contract ID")
                continue
            
            print(f"Contract ID: {contract_id}")
            
        except APIError as e:
            print(f"Failed to buy: {e}")
            continue

        # Wait for trade to complete (UNCHANGED)
        await asyncio.sleep(2)

        # Flag to track if we've already processed this trade's result
        trade_result_processed = False
        trade_profit = 0

        # Get contract details for verification
        try:
            contract_details = await api.proposal_open_contract({"proposal_open_contract": 1, "contract_id": contract_id})
            if contract_details and 'proposal_open_contract' in contract_details:
                contract_info = contract_details['proposal_open_contract']
                buy_price = contract_info.get('buy_price', current_bet_amount)
                sell_price = contract_info.get('sell_price', 0)
                is_sold = contract_info.get('is_sold', False)
                profit = contract_info.get('profit', 0)
                
                print(f"Contract Status: {'Sold' if is_sold else 'Active'}")
                print(f"Buy Price: ${buy_price}")
                print(f"Sell Price: ${sell_price}")
                print(f"Profit: ${profit}")
                
                # Process win/loss only if contract is sold
                if is_sold:
                    trade_profit = profit
                    trade_result_processed = True
                    
                    if profit > 0:
                        print("✅ WIN!")
                        wins += 1
                        consecutive_losses = 0
                        martingale_step = 0
                        current_bet_amount = BET_AMOUNT
                    else:
                        print("❌ LOSS!")
                        losses += 1
                        consecutive_losses += 1
                        
                        # Martingale logic
                        if MARTINGALE_ENABLED and martingale_step < MAX_MARTINGALE_STEPS:
                            martingale_step += 1
                            current_bet_amount *= MARTINGALE_MULTIPLIER
                            print(f"Martingale activated! Step {martingale_step}, new bet: ${current_bet_amount}")
                        else:
                            # Reset if max steps reached or Martingale disabled
                            martingale_step = 0
                            current_bet_amount = BET_AMOUNT
                            if MARTINGALE_ENABLED:
                                print("Max Martingale steps reached. Resetting bet amount.")
                else:
                    print("Contract still active, checking profit table...")
                    
        except APIError as e:
            print(f"Failed to get contract details: {e}")
            # Will fall back to profit table
            pass

        # Check profit/loss from the profit_table API only if we haven't processed the result yet
        if not trade_result_processed:
            try:
                profit_table = await api.profit_table({"profit_table": 1, "limit": 1})
                if profit_table and 'profit_table' in profit_table and profit_table['profit_table'].get('transactions'):
                    last_trade = profit_table['profit_table']['transactions'][0]
                    sell_price = last_trade.get('sell_price', 0)
                    buy_price = last_trade.get('buy_price', current_bet_amount)
                    transaction_id = last_trade.get('transaction_id', 'N/A')
                    
                    print(f"Transaction ID: {transaction_id}")
                    print(f"Buy Price: ${buy_price}")
                    print(f"Sell Price: ${sell_price}")

                    profit = sell_price - buy_price
                    print(f"Profit from last trade: ${profit}")
                    
                    # Process the trade result
                    if profit > 0:
                        print("✅ WIN!")
                        wins += 1
                        consecutive_losses = 0
                        martingale_step = 0
                        current_bet_amount = BET_AMOUNT
                    else:
                        print("❌ LOSS!")
                        losses += 1
                        consecutive_losses += 1
                        
                        # Martingale logic
                        if MARTINGALE_ENABLED and martingale_step < MAX_MARTINGALE_STEPS:
                            martingale_step += 1
                            current_bet_amount *= MARTINGALE_MULTIPLIER
                            print(f"Martingale activated! Step {martingale_step}, new bet: ${current_bet_amount}")
                        else:
                            # Reset if max steps reached or Martingale disabled
                            martingale_step = 0
                            current_bet_amount = BET_AMOUNT
                            if MARTINGALE_ENABLED:
                                print("Max Martingale steps reached. Resetting bet amount.")
                else:
                    print("No transaction data found")
            except APIError as e:
                print(f"Failed to get profit_table: {e}")
                continue
        
        # Print round summary
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        print(f"Round {round_num} Summary: {wins}W/{losses}L (Win Rate: {win_rate:.1f}%)")
        print("-" * 50)

    # Final statistics
    print("\n" + "=" * 50)
    print("TRADING SESSION COMPLETED")
    print("=" * 50)
    
    try:
        final_balance = await api.balance()
        final_amount = final_balance['balance']['balance']
        total_pnl = final_amount - initial_balance
        
        print(f"Initial Balance: ${initial_balance}")
        print(f"Final Balance: ${final_amount}")
        print(f"Total P&L: ${total_pnl:+.2f}")
        print(f"ROI: {(total_pnl/initial_balance*100):+.2f}%")
        
    except APIError as e:
        print(f"Failed to get final balance: {e}")
    
    print(f"\nTrade Statistics:")
    print(f"Total Rounds: {TOTAL_ROUNDS}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Final Martingale Step: {martingale_step}")
    print(f"Consecutive Losses: {consecutive_losses}")

# Run immediately (REPLACED SCHEDULER WITH DIRECT EXECUTION)
if __name__ == "__main__":
    asyncio.run(trading_bot())

