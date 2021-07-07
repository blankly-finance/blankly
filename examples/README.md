## Setting up is easy:
1. *Rename or create a new file of the format* `keys_example.json` as `keys.json`. ***This is done to keep it out of version control (putting keys in git history can be bad).***
2. Add your exchange keys to the new (non-version controlled) `keys.json` file
3. Run `basic_example.py`. You can change exchanges by changing the line `Blankly.CoinbasePro()` to what you're using, such as `Blankly.Binance()`