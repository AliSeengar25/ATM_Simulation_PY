import os
import tempfile
from atm_backend import ATMAccount
passed = 0
failed = 0
def check(test_name, condition):
    """Print PASS or FAIL for one test."""
    global passed, failed
    if condition:
        passed += 1
        print("PASS -", test_name)
    else:
        failed += 1
        print("FAIL -", test_name)
def new_account():
    """Fresh ATM using a brand new temporary file."""
    folder = tempfile.mkdtemp()
    path = os.path.join(folder, "test_data.json")
    return ATMAccount(path), path
def login(atm, number="1000066968", pin="2425"):
    """Helper: do both login steps."""
    atm.check_account_number(number)
    return atm.check_pin(pin)
atm, path = new_account()
found, message = atm.check_account_number("1000123456")
check("Existing account number accepted", found)
ok, message = atm.check_pin("1234")
check("Correct PIN logs in", ok and atm.logged_in)
check("Logged-in account is the right one", atm.get_account()["holder_name"] == "Ahmed Khan")

# Wrong account number
atm, path = new_account()
found, message = atm.check_account_number("9999999999")
check("Unknown account number rejected", not found and "not found" in message)
found, message = atm.check_account_number("123")
check("Short account number rejected", not found)
found, message = atm.check_account_number("10001234ab")
check("Non-digit account number rejected", not found)
ok, message = atm.check_pin("1234")
check("PIN refused when no account was selected", not ok and not atm.logged_in)

# Wrong PIN and three attempt lockout
atm, path = new_account()
atm.check_account_number("1000123456")
atm.check_pin("0000")
atm.check_pin("1111")
check("Two wrong PINs do not lock yet", not atm.locked)
atm.check_pin("2222")
check("Third wrong PIN locks the session", atm.locked)
ok, message = atm.check_pin("1234")
check("Correct PIN refused after lockout", not ok)
found, message = atm.check_account_number("1000234567")
check("Account entry refused after lockout", not found)
#PIN of another account does not work
atm, path = new_account()
atm.check_account_number("1000123456")
ok, message = atm.check_pin("5678")        # this is Fatima's PIN
check("Another account's PIN is rejected", not ok)
#Successful withdrawal
atm, path = new_account()
login(atm)
result = atm.withdraw("4700")
check("Withdrawal of 4700 succeeds", result["success"])
check("Balance is 145300 after withdrawal", atm.get_balance() == 145300)
#Insufficient balance (Bilal has only PKR 12,000)
atm, path = new_account()
login(atm, "1000345678", "2468")
result = atm.withdraw("15000")
check("Insufficient balance rejected",
      not result["success"] and "Insufficient" in result["message"])
check("Balance unchanged after rejection", atm.get_balance() == 12000)
#Invalid deposit amounts
atm, path = new_account()
login(atm)
for bad in ["abc", "-500", "0", "", "12.5"]:
    result = atm.deposit(bad)
    check("Deposit '" + bad + "' rejected", not result["success"])
check("Balance unchanged after bad deposits", atm.get_balance() == 150000)
result = atm.deposit("2500")
check("Valid deposit of 2500 works", result["success"] and atm.get_balance() == 152500)
#Daily withdrawal limit
atm, path = new_account()
login(atm)
atm.withdraw("20000")
result = atm.withdraw("6000")
check("Withdrawal above the remaining daily limit rejected", not result["success"])
result = atm.withdraw("5000")
check("Withdrawal up to exactly 25000 total allowed", result["success"])
result = atm.withdraw("100")
check("Daily limit reached message",
      not result["success"] and "reached" in result["message"])
#Daily limit resets on a new date
atm.get_account()["daily_withdrawal"]["date"] = "2000-01-01"
result = atm.withdraw("1000")
check("Daily total resets on a new date", result["success"]
      and atm.get_withdrawn_today() == 1000)
#Cash denomination
atm, path = new_account()
login(atm)
check("4700 = 0x5000, 4x1000, 1x500, 2x100",
      atm.calculate_notes(4700) == {5000: 0, 1000: 4, 500: 1, 100: 2})
check("12600 = 2x5000, 2x1000, 1x500, 1x100",
      atm.calculate_notes(12600) == {5000: 2, 1000: 2, 500: 1, 100: 1})
check("250 cannot be dispensed", atm.calculate_notes(250) is None)
result = atm.withdraw("250")
check("Withdraw 250 rejected", not result["success"])
#Transaction history
atm, path = new_account()
login(atm)
for number in range(1, 8):
    atm.deposit(str(number * 100))
statement = atm.get_mini_statement()
check("Mini statement shows only 5 transactions", len(statement) == 5)
check("Newest transaction is first", statement[0]["amount"] == 700)
check("Transaction has all fields",
      all(key in statement[0] for key in
          ["id", "type", "amount", "date", "time", "balance_after", "account"]))
all_ids = [t["id"] for t in atm.get_account()["transactions"]]
check("Transaction IDs are unique", len(set(all_ids)) == 7)
check("Receipt hides most of the account number", statement[0]["account"] == "******3456")
#Accounts are separate from each other
atm, path = new_account()
login(atm)
atm.withdraw("1000")
atm.logout()
login(atm, "1000234567", "5678")
check("Other account balance untouched", atm.get_balance() == 500000)
check("Other account has no transactions", len(atm.get_mini_statement()) == 0)
check("Other account has its own daily total", atm.get_withdrawn_today() == 0)
#Change PIN
atm, path = new_account()
login(atm)
result = atm.change_pin("0000", "4321", "4321")
check("Change PIN: wrong current PIN rejected", not result["success"])
result = atm.change_pin("1234", "12", "12")
check("Change PIN: short new PIN rejected", not result["success"])
result = atm.change_pin("1234", "abcd", "abcd")
check("Change PIN: non-digit new PIN rejected", not result["success"])
result = atm.change_pin("1234", "1234", "1234")
check("Change PIN: same PIN rejected", not result["success"])
result = atm.change_pin("1234", "4321", "9999")
check("Change PIN: mismatch rejected", not result["success"])
result = atm.change_pin("1234", "4321", "4321")
check("Change PIN: valid change works", result["success"])
atm.logout()
atm_again = ATMAccount(path)
login(atm_again, "1000123456", "1234")
check("Old PIN no longer works after change", not atm_again.logged_in)
ok, message = login(atm_again, "1000123456", "4321")
check("New PIN works after restart", ok)
#Account details
atm, path = new_account()
login(atm)
details = atm.get_account_details()
check("Details: name, type, currency",
      details["holder_name"] == "Ahmed Khan" and details["account_type"] == "Savings"
      and details["currency"] == "PKR")
check("Details: balance and limit", details["balance"] == 150000
      and details["remaining_today"] == 25000)
#simulate closing and reopening the program
atm, path = new_account()
login(atm)
atm.withdraw("1500")
atm.deposit("300")
atm_again = ATMAccount(path)        
login(atm_again)
check("Balance saved after restart", atm_again.get_balance() == 148800)
check("History saved after restart", len(atm_again.get_mini_statement()) == 2)
check("Daily total saved after restart", atm_again.get_withdrawn_today() == 1500)
#Damaged file and oldformat file
atm, path = new_account()
with open(path, "w") as file:
    file.write("this is not json")
atm_again = ATMAccount(path)
check("Damaged JSON file falls back to demo accounts",
      "1000123456" in atm_again.data["accounts"])
with open(path, "w") as file:
    file.write('{"balance": 50000, "pin": "1234", "transactions": []}')
atm_again = ATMAccount(path)
check("Old single-account file is replaced by demo accounts",
      "1000123456" in atm_again.data["accounts"])
print()
print("Passed:", passed, " Failed:", failed)