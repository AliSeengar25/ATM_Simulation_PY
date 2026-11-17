import json
import os
from datetime import datetime
FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(FOLDER, "atm_data.json")
CURRENCY = "PKR"                           
DAILY_LIMIT = 25000                      
MAX_PIN_ATTEMPTS = 3                         
ACCOUNT_NUMBER_LENGTH = 10                 
PIN_LENGTH = 4                             
DENOMINATIONS = [5000, 1000, 500, 100]     
DEFAULT_DATA = {
    "next_transaction_number": 1,
    "accounts": {
        "1000066968": {
            "holder_name": "Ali Seengar",
            "account_type": "Savings",
            "branch": "Defence veiw phase 2 Main Branch",
            "pin": "2425",
            "balance": 200000,
            "daily_withdrawal": {"date": "", "total": 0},
            "transactions": [],
        },
        "1000066952": {
            "holder_name": "Muhammad Asim",
            "account_type": "Current",
            "branch": "Lahore Gulberg Branch",
            "pin": "7777",
            "balance": 110000,
            "daily_withdrawal": {"date": "", "total": 0},
            "transactions": [],
        },
        "1000066955": {
            "holder_name": "Aliza ",
            "account_type": "Savings",
            "branch": "Islamabad F-7 Branch",
            "pin": "5555"
            "",
            "balance": 12000,
            "daily_withdrawal": {"date": "", "total": 0},
            "transactions": [],
        },
    },
}

class ATMAccount:
    """The ATM session: loads all accounts and works on ONE logged-in account."""

    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.data = {}
        self.selected_number = None   
        self.current_number = None    
        self.wrong_attempts = 0       
        self.locked = False           
        self.logged_in = False
        self.load_data()
        self.reset_daily_totals_if_new_day()
        # jeson file handling 

    def use_default_data(self):
        """Start with the built-in demo accounts and save them."""
        # json round-trip makes a copy, so DEFAULT_DATA is never changed
        self.data = json.loads(json.dumps(DEFAULT_DATA))
        self.save_data()

    def load_data(self):
        """Read the JSON file. If it is missing, damaged or in an old
        format, use the default demo accounts."""
        try:
            with open(self.data_file, "r") as file:
                self.data = json.load(file)
            if "accounts" not in self.data or "next_transaction_number" not in self.data:
                self.use_default_data()
        except (FileNotFoundError, json.JSONDecodeError):
            self.use_default_data()

    def save_data(self):
        """Write the dictionary to the JSON file.
        We write to a temporary file first and then rename it, so the
        real file can never be left half-written."""
        temp_file = self.data_file + ".tmp"
        try:
            with open(temp_file, "w") as file:
                json.dump(self.data, file, indent=4)
            os.replace(temp_file, self.data_file)
            return True
        except OSError:
            return False
    def get_account(self):
        """The dictionary of the logged-in account."""
        return self.data["accounts"][self.current_number]

    def mask_account_number(self, number):
        """1000123456 -> ******3456 (only the last 4 digits are shown)"""
        return "*" * (len(number) - 4) + number[-4:]

    def get_account_details(self):
        """Everything the 'Account Details' screen needs."""
        account = self.get_account()
        return {
            "holder_name": account["holder_name"],
            "account_number": self.current_number,
            "account_type": account["account_type"],
            "branch": account["branch"],
            "currency": CURRENCY,
            "balance": account["balance"],
            "daily_limit": DAILY_LIMIT,
            "withdrawn_today": self.get_withdrawn_today(),
            "remaining_today": self.get_remaining_daily_limit(),
            "total_transactions": len(account["transactions"]),
        }
    # date and time
    def today_text(self):
        return datetime.now().strftime("%Y-%m-%d")

    def reset_daily_totals_if_new_day(self):
        """For every account: if the saved date is not today, start a
        fresh daily withdrawal total."""
        today = self.today_text()
        changed = False
        for account in self.data["accounts"].values():
            if account["daily_withdrawal"]["date"] != today:
                account["daily_withdrawal"] = {"date": today, "total": 0}
                changed = True
        if changed:
            self.save_data()   
    # LOGIN
    def check_account_number(self, number_text):
        """Step 1. Returns (found, message)."""
        if self.locked:
            return False, "Session locked. Please restart the ATM."
        number_text = str(number_text).strip()
        if len(number_text) != ACCOUNT_NUMBER_LENGTH or not number_text.isdigit():
            return False, "Account number must have 10 digits."
        if number_text not in self.data["accounts"]:
            return False, "Account number not found."
        self.selected_number = number_text
        return True, "Account found."

    def check_pin(self, entered_pin):
        """Step 2. Check the PIN of the selected account.
        Returns (success, message)."""
        if self.locked:
            return False, "Session locked. Please restart the ATM."
        if self.selected_number is None:
            return False, "Please enter your account number first."

        account = self.data["accounts"][self.selected_number]
        if entered_pin == account["pin"]:
            self.wrong_attempts = 0
            self.logged_in = True
            self.current_number = self.selected_number
            self.reset_daily_totals_if_new_day()
            return True, "Login successful."

        # Wrong PIN
        self.wrong_attempts += 1
        attempts_left = MAX_PIN_ATTEMPTS - self.wrong_attempts
        if attempts_left <= 0:
            self.locked = True
            return False, "Too many wrong attempts. Session locked."
        if attempts_left == 1:
            return False, "Incorrect PIN. 1 attempt remaining."
        return False, "Incorrect PIN. " + str(attempts_left) + " attempts remaining."

    def logout(self):
        self.logged_in = False
        self.current_number = None
        self.selected_number = None
    # CHANGE PIN
    def change_pin(self, current_pin, new_pin, confirm_pin):
        """Change the PIN of the logged-in account.
        Returns a dictionary with success and message."""
        account = self.get_account()
        if current_pin != account["pin"]:
            return {"success": False, "message": "Current PIN is incorrect."}
        if len(new_pin) != PIN_LENGTH or not new_pin.isdigit():
            return {"success": False, "message": "New PIN must be exactly 4 digits."}
        if new_pin == current_pin:
            return {"success": False,
                    "message": "New PIN must be different from the current PIN."}
        if new_pin != confirm_pin:
            return {"success": False,
                    "message": "New PIN and confirmation do not match."}

        account["pin"] = new_pin
        if not self.save_data():
            return {"success": False, "message": "Could not save data file."}
        return {"success": True, "message": "PIN changed successfully."}
    # BALANCE AND DAILY LIMIT
    def get_balance(self):
        return self.get_account()["balance"]

    def get_withdrawn_today(self):
        self.reset_daily_totals_if_new_day()
        return self.get_account()["daily_withdrawal"]["total"]

    def get_remaining_daily_limit(self):
        return DAILY_LIMIT - self.get_withdrawn_today()
    # AMOUNT VALIDATION
    def validate_amount(self, amount_text):
        """Turn the typed text into a whole number.
        Returns (True, number) or (False, error message)."""
        amount_text = str(amount_text).strip()
        if amount_text == "":
            return False, "Please enter an amount."
        try:
            amount = int(amount_text)
        except ValueError:
            return False, "Invalid amount. Use whole numbers only."
        if amount <= 0:
            return False, "Amount must be greater than zero."
        return True, amount
    # CASH DENOMINATION
    def calculate_notes(self, amount):
        """Work out how many notes of each type are needed.
        Returns a dictionary like {5000: 0, 1000: 4, 500: 1, 100: 2}
        or None if the amount cannot be paid with these notes."""
        notes = {}
        remaining = amount
        for note_value in DENOMINATIONS:          # biggest note first
            notes[note_value] = remaining // note_value
            remaining = remaining % note_value
        if remaining != 0:
            return None                           # e.g. PKR 250 -> impossible
        return notes
    # TRANSACTIONS
    def record_transaction(self, transaction_type, amount):
        """Add a transaction to the account history and return it."""
        account = self.get_account()
        now = datetime.now()
        number = self.data["next_transaction_number"]
        transaction = {
            "id": "TXN" + str(number).zfill(6),
            "type": transaction_type,
            "amount": amount,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "balance_after": account["balance"],
            "account": self.mask_account_number(self.current_number),
        }
        self.data["next_transaction_number"] = number + 1
        account["transactions"].append(transaction)
        return transaction

    def deposit(self, amount_text):
        """Deposit money. Returns a dictionary with the result."""
        ok, result = self.validate_amount(amount_text)
        if not ok:
            return {"success": False, "message": result}
        amount = result

        account = self.get_account()
        account["balance"] = account["balance"] + amount
        receipt = self.record_transaction("Deposit", amount)
        if not self.save_data():
            return {"success": False, "message": "Could not save data file."}
        return {"success": True, "message": "Deposit successful.",
                "receipt": receipt}

    def withdraw(self, amount_text):
        """Withdraw money. Returns a dictionary with the result."""
        self.reset_daily_totals_if_new_day()
        account = self.get_account()

        #Is the amount a valid number?
        ok, result = self.validate_amount(amount_text)
        if not ok:
            return {"success": False, "message": result}
        amount = result

        #Can it be paid with the available notes?
        notes = self.calculate_notes(amount)
        if notes is None:
            return {"success": False,
                    "message": "Amount must be a multiple of PKR 100 "
                               "(notes: 5000, 1000, 500, 100)."}

        #Is there enough money in the account?
        if amount > account["balance"]:
            return {"success": False, "message": "Insufficient balance."}

        # Is the daily limit respected?
        remaining_limit = self.get_remaining_daily_limit()
        if amount > remaining_limit:
            if remaining_limit <= 0:
                message = "Daily withdrawal limit of PKR 25,000 reached."
            else:
                message = ("Daily limit exceeded. You can still withdraw "
                           "PKR " + format(remaining_limit, ",") + " today.")
            return {"success": False, "message": message}
# All checks passed
        account["balance"] = account["balance"] - amount
        account["daily_withdrawal"]["total"] += amount
        receipt = self.record_transaction("Withdrawal", amount)
        if not self.save_data():
            return {"success": False, "message": "Could not save data file."}
        return {"success": True, "message": "Withdrawal successful.",
                "receipt": receipt, "notes": notes}

    def get_mini_statement(self):
        """Return the last five transactions of this account, newest first."""
        last_five = self.get_account()["transactions"][-5:]
        last_five.reverse()
        return last_five