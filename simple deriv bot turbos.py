import sys
import os
import asyncio
import random
from deriv_api import DerivAPI, APIError

# ============================================================
# TURBO OPTIONS BOT - Fixed Version
# ============================================================

# Configuration
APP_ID = 63411
API_TOKEN = os.getenv('DERIV_TOKEN', 'API TOKEN HERE')

# Trading Parameters
STAKE = 10                     # Stake amount in USD
DURATION = 5                   # Duration in ticks
DURATION_UNIT = "t"            # "t" for ticks (turbo options use ticks)
SYMBOL = "R_100"               # Volatility 100 Index
TOTAL_ROUNDS = 10              # Number of trades
MARTINGALE_ENABLED = True      # Martingale on loss
MAX_MARTINGALE_STEPS = 3       # Max martingale steps
MARTINGALE_MULTIPLIER = 2      # Double bet after loss

# Available barriers for R_100 - MUST include + sign for DOWN contracts
# Format based on API error: +2.15, +3.77, etc.
TURBOSLONG_BARRIERS = ["-2.15", "-3.77", "-6.64", "-11.68", "-20.56", "-36.18", "-63.68", "-112.08", "-197.27", "-347.21"]
TURBOSSHORT_BARRIERS = ["+2.15", "+3.77", "+6.64", "+11.68", "+20.56", "+36.18", "+63.68", "+112.08", "+197.27", "+347.21"]

if not API_TOKEN:
    sys.exit("DERIV_TOKEN environment variable is not set")

async def trading_bot():
    """Turbo Options trading bot with correct barrier formatting"""
    
    api = DerivAPI(app_id=APP_ID)
    await api.authorize(API_TOKEN)

    # Get initial balance
    balance = await api.balance()
    initial_balance = balance['balance']['balance']
    
    current_bet = STAKE
    martingale_step = 0
    wins = 0
    losses = 0
    breached_count = 0
    
    print("=" * 60)
    print("TURBO OPTIONS TRADING BOT")
    print("=" * 60)
    print(f"Initial Balance: ${initial_balance:.2f}")
    print(f"Base Stake: ${STAKE}")
    print(f"Duration: {DURATION} {DURATION_UNIT}")
    print(f"Symbol: {SYMBOL}")
    print(f"Martingale: {'ENABLED' if MARTINGALE_ENABLED else 'DISABLED'}")
    print("=" * 60)
    print("\n📌 HOW TURBO WORKS:")
    print("   - Predict UP (Long): Price must stay above barrier (negative value)")
    print("   - Predict DOWN (Short): Price must stay below barrier (positive value)")
    print("   - If barrier is breached → LOSS (early termination)")
    print("=" * 60)

    for round_num in range(1, TOTAL_ROUNDS + 1):
        print(f"\n{'='*60}")
        print(f"ROUND {round_num}/{TOTAL_ROUNDS}")
        print(f"{'='*60}")
        
        # Get current balance
        current_balance = await api.balance()
        print(f"Current Balance: ${current_balance['balance']['balance']:.2f}")
        print(f"Bet Amount: ${current_bet:.2f}")
        
        # Random prediction: True = UP (TURBOSLONG), False = DOWN (TURBOSSHORT)
        predict_up = random.choice([True, False])
        contract_type = "TURBOSLONG" if predict_up else "TURBOSSHORT"
        direction = "UP (Long)" if predict_up else "DOWN (Short)"
        
        # Select random barrier from available options
        available_barriers = TURBOSLONG_BARRIERS if predict_up else TURBOSSHORT_BARRIERS
        barrier = random.choice(available_barriers)
        
        # Description for display
        if predict_up:
            barrier_description = f"{barrier} below entry"
        else:
            barrier_description = f"{barrier} above entry"
        
        print(f"\n📊 PREDICTION:")
        print(f"   Direction: {direction}")
        print(f"   Contract Type: {contract_type}")
        print(f"   Barrier: {barrier} ({barrier_description})")
        
        try:
            # Build proposal request
            proposal_params = {
                "proposal": 1,
                "amount": float(current_bet),
                "barrier": barrier,                  # Use barrier with + or - sign
                "basis": "stake",
                "contract_type": contract_type,      # TURBOSLONG or TURBOSSHORT
                "currency": "USD",
                "duration": DURATION,
                "duration_unit": DURATION_UNIT,      # "t" for ticks
                "symbol": SYMBOL
            }
            
            # Get proposal
            proposal = await api.proposal(proposal_params)
            
            # Check for errors
            if 'error' in proposal:
                print(f"\n❌ Proposal error: {proposal['error']['message']}")
                continue
                
            # Safely extract proposal data
            proposal_data = proposal.get('proposal', {})
            if not proposal_data:
                print("\n❌ No proposal data received")
                continue
                
            proposal_id = proposal_data.get('id')
            if not proposal_id:
                print("\n❌ No proposal ID received")
                continue
            
            # Get ask price safely
            ask_price = proposal_data.get('ask_price', 0)
            payout = proposal_data.get('payout', 0)
            entry_spot = proposal_data.get('entry_spot', 'N/A')
            barrier_used = proposal_data.get('barrier', barrier)
            
            print(f"\n💰 PROPOSAL RECEIVED:")
            print(f"   Proposal ID: {proposal_id}")
            print(f"   Ask Price: ${ask_price:.2f}")
            print(f"   Payout: ${payout:.2f}")
            print(f"   Entry Spot: {entry_spot}")
            print(f"   Barrier: {barrier_used}")
            
            # Place the trade
            buy_response = await api.buy({
                "buy": proposal_id,
                "price": current_bet
            })
            
            if 'error' in buy_response:
                print(f"\n❌ Buy error: {buy_response['error']['message']}")
                continue
                
            # Safely extract buy data
            buy_data = buy_response.get('buy', {})
            contract_id = buy_data.get('contract_id')
            
            if not contract_id:
                print("\n❌ No contract ID received")
                continue
                
            print(f"\n✅ TRADE EXECUTED!")
            print(f"   Contract ID: {contract_id}")
            
            # Wait for contract to complete
            print(f"\n⏳ Waiting for contract to complete ({DURATION} ticks)...")
            await asyncio.sleep(DURATION * 2)  # Rough estimate: 2 seconds per tick
            
            # Get final contract result
            contract_response = await api.proposal_open_contract({
                "proposal_open_contract": 1,
                "contract_id": contract_id
            })
            
            if 'error' in contract_response:
                print(f"\n❌ Error getting final contract: {contract_response['error']['message']}")
                continue
                
            # Safely extract contract info
            contract_info = contract_response.get('proposal_open_contract', {})
            if not contract_info:
                print("\n❌ No contract information received")
                continue
            
            # Extract contract details with safe defaults
            status = contract_info.get('status', 'unknown')
            profit = contract_info.get('profit', 0)
            buy_price = contract_info.get('buy_price', current_bet)
            sell_price = contract_info.get('sell_price', 0)
            entry_spot = contract_info.get('entry_spot', 'N/A')
            
            # Handle exit tick safely
            exit_tick = contract_info.get('exit_tick', {})
            if isinstance(exit_tick, dict):
                exit_spot = exit_tick.get('quote', 'N/A')
            else:
                exit_spot = 'N/A'
            
            barrier_used = contract_info.get('barrier', barrier)
            
            print(f"\n{'='*50}")
            print(f"CONTRACT RESULT")
            print(f"{'='*50}")
            print(f"Status: {status}")
            print(f"Entry Spot: {entry_spot}")
            print(f"Exit Spot: {exit_spot}")
            print(f"Barrier: {barrier_used}")
            print(f"Buy Price: ${buy_price:.2f}")
            print(f"Sell Price: ${sell_price:.2f}")
            print(f"Profit/Loss: ${profit:+.2f}")
            
            # Determine win/loss
            is_win = profit > 0
            
            if is_win:
                print(f"\n🎉 WIN! Price stayed within barrier limits.")
                wins += 1
                martingale_step = 0
                current_bet = STAKE
            else:
                if status == "breached":
                    print(f"\n💥 LOSS! Barrier was breached during contract.")
                    breached_count += 1
                else:
                    print(f"\n❌ LOSS! Trade ended out of the money.")
                losses += 1
                
                # Martingale logic
                if MARTINGALE_ENABLED and martingale_step < MAX_MARTINGALE_STEPS:
                    martingale_step += 1
                    current_bet *= MARTINGALE_MULTIPLIER
                    print(f"\n📈 MARTINGALE ACTIVATED!")
                    print(f"   Step: {martingale_step}/{MAX_MARTINGALE_STEPS}")
                    print(f"   Next Bet: ${current_bet:.2f}")
                else:
                    martingale_step = 0
                    current_bet = STAKE
                    if MARTINGALE_ENABLED and losses > 0:
                        print(f"\n🔄 Max martingale steps reached. Resetting to base bet.")
            
            # Show statistics
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0
            print(f"\n📊 STATISTICS:")
            print(f"   Wins: {wins}")
            print(f"   Losses: {losses}")
            print(f"   Barrier Breaches: {breached_count}")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Martingale Step: {martingale_step}")
            
        except APIError as e:
            print(f"\n❌ API Error: {e}")
            continue
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Early termination requested!")
            if 'contract_id' in locals():
                print(f"\n📝 Note: Contract {contract_id} may still be active.")
                print("   You can close it manually using the sell API.")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRADING SESSION COMPLETED")
    print("=" * 60)
    
    final_balance = await api.balance()
    final_amount = final_balance['balance']['balance']
    total_pnl = final_amount - initial_balance
    
    print(f"\n💰 FINAL BALANCE:")
    print(f"   Initial Balance: ${initial_balance:.2f}")
    print(f"   Final Balance: ${final_amount:.2f}")
    print(f"   Total P&L: ${total_pnl:+.2f}")
    print(f"   ROI: {(total_pnl/initial_balance*100):+.2f}%")
    
    print(f"\n📈 TRADE STATISTICS:")
    print(f"   Total Rounds: {round_num}")
    print(f"   Wins: {wins}")
    print(f"   Losses: {losses}")
    print(f"   Barrier Breaches: {breached_count}")
    if wins + losses > 0:
        print(f"   Win Rate: {(wins/(wins+losses)*100):.1f}%")
    print(f"   Final Martingale Step: {martingale_step}")

if __name__ == "__main__":
    asyncio.run(trading_bot())