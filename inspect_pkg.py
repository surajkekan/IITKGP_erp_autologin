import iitkgp_erp_login
import iitkgp_erp_login.utils
import inspect

print("Top level package contents:")
print(dir(iitkgp_erp_login))

print("\nUtils contents:")
print(dir(iitkgp_erp_login.utils))

print("\nHelp on iitkgp_erp_login.ERPLogin:")
# Assuming there is a main class, let's guess its name or find it.
# Based on usage `from iitkgp_erp_login import ERPLogin` (common pattern)
try:
    from iitkgp_erp_login import ERPLogin
    print(help(ERPLogin))
except ImportError:
    print("ERPLogin class not found directly.")

