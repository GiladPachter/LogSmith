import json

import LogSmith


print("\n\n\nPackagr metadata:\n=================\n")
print(json.dumps(LogSmith.__metadata__, indent = 4))

print("\n\n\nLicense text:\n=============\n")
print(LogSmith.__license_text__)

print("\n\n\nPackagr content:\n================\n")
print(LogSmith.__package_content__)
