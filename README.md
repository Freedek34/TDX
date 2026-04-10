# TDX - Simple Deriv Trading Bots

A collection of simple automated trading bots for the [Deriv](https://deriv.com) platform, built with Python using the Deriv API. Each bot trades a different contract type on synthetic indices (Volatility 100 Index).

## 📋 Available Bots

| Bot | File | Contract Type | Description |
|-----|------|--------------|-------------|
| **Rise/Fall** | `simple derivbot risefall.py` | CALL / PUT | Predicts whether the market will rise or fall over 1 tick |
| **Even/Odd** | `simple derivbot evenodd.py` | DIGITEVEN / DIGITODD | Predicts whether the last digit of the price will be even or odd |
| **Higher/Lower** | `simple derivbot higherlower.py` | CALL / PUT | Predicts whether the market will go higher or lower over 5 ticks |
| **Over/Under** | `simple derivbot overunder.py` | DIGITOVER / DIGITUNDER | Predicts whether the last digit will be over or under 5 |
| **Multipliers** | `simple deriv bot multipliers.py` | MULTUP / MULTDOWN | Trades multiplier contracts with take-profit and stop-loss |
| **Turbos** | `simple deriv bot turbos.py` | TURBOSLONG / TURBOSSHORT | Trades turbo option contracts with barrier levels |
| **Matches/Differs** | `simple deriv bot matches differs.py` | *(Coming soon)* | — |
| **Accumulators** | `simple deriv bot accumulators.py` | *(Coming soon)* | — |
| **Touch/No Touch** | `simple deriv bot touch no touch.py` | *(Coming soon)* | — |

## ⚙️ Features

- **Martingale Strategy** — Optionally doubles the bet after each loss to recover (configurable)
- **Configurable Parameters** — Adjust bet amount, number of rounds, max Martingale steps, and multiplier
- **Real-time Balance Tracking** — Displays profit/loss after each trade and at session end
- **Tick History Analysis** — Collects recent tick data before trading

---

## 🔑 How to Get Your Deriv API Token

You need a **Deriv API token** to run these bots. Follow these steps:

### Step 1: Create a Deriv Account
1. Go to [https://deriv.com](https://deriv.com) and sign up for an account (or log in if you already have one).
2. You can use a **demo account** to test with virtual money first.

### Step 2: Generate an API Token
1. Log in to your Deriv account.
2. Navigate to **API Token Management** at:  
   👉 [https://app.deriv.com/account/api-token](https://app.deriv.com/account/api-token)
3. Under **"Select scopes for your token"**, check the following permissions:
   - ✅ **Read**
   - ✅ **Trade**
   - ✅ **Payments** *(optional, only if you need balance/payment features)*
   - ✅ **Trading information**
   - ✅ **Admin** *(optional)*
4. Enter a name for your token (e.g., `TDX Bot`).
5. Click **"Create"**.
6. **Copy the token** — you will only see it once! Store it somewhere safe.

### Step 3: Plug the API Token into the Bot

In each bot file, you'll find this line near the top:

```python
API_TOKEN = os.getenv('DERIV_TOKEN', 'API TOKEN HERE')
```

You have **two options** to set your token:

#### Option A: Replace directly in the code (quick & easy)
Replace `'API TOKEN HERE'` with your actual token:

```python
API_TOKEN = os.getenv('DERIV_TOKEN', 'your_actual_api_token_here')
```

For example:
```python
API_TOKEN = os.getenv('DERIV_TOKEN', 'a1b2c3d4e5f6g7h8')
```

#### Option B: Use an environment variable (recommended & more secure)
Set the `DERIV_TOKEN` environment variable in your terminal before running the bot:

```bash
export DERIV_TOKEN="your_actual_api_token_here"
```

This way your token is never hardcoded in the source files. You can also add it to your `~/.bashrc` or `~/.zshrc` to make it persistent:

```bash
echo 'export DERIV_TOKEN="your_actual_api_token_here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🚀 Installation & Setup

### 1. Install Python Dependencies

```bash
pip install python-deriv-api websockets
```

### 2. Set Your API Token
See [How to Get Your Deriv API Token](#-how-to-get-your-deriv-api-token) above.

### 3. Run a Bot

```bash
python "simple derivbot risefall.py"
```

Or any other bot file:

```bash
python "simple derivbot evenodd.py"
python "simple derivbot higherlower.py"
python "simple derivbot overunder.py"
python "simple deriv bot multipliers.py"
python "simple deriv bot turbos.py"
```

---

## 🛠️ Configuration

Each bot has configurable parameters at the top of the file:

```python
APP_ID = 63411                  # Deriv App ID
API_TOKEN = os.getenv('DERIV_TOKEN', 'API TOKEN HERE')  # Your API token
BET_AMOUNT = 10                 # Starting bet amount in USD
TOTAL_ROUNDS = 10               # Number of trades to execute
MARTINGALE_ENABLED = True       # Enable/disable Martingale strategy
MAX_MARTINGALE_STEPS = 5        # Max consecutive Martingale doublings
MARTINGALE_MULTIPLIER = 2       # Bet multiplier after each loss
```

---

## ⚠️ Disclaimer

> **Trading involves substantial risk of loss.** These bots are for **educational purposes only**. Past performance does not guarantee future results. Use a **demo account** for testing. Never trade with money you cannot afford to lose. The authors are not responsible for any financial losses incurred from using these bots.

---

## 📄 License

This project is open source and available for personal and educational use.
