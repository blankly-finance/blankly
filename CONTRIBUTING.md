# Contributions

Firstly, thank you for taking the time and expressing interest in contributing to the Blankly project 🎉🎉!

**_Before you contribute_ we need you to sign the CLA.**

Contributions are welcome. To ensure a quick and easy merge, just make sure you look through the way the files are
organized, and you make the changes where they make sense and are easy to maintain!

## Getting Started with Contributions

### Installing from Source

The first step to getting started is to install from source. Our best suggestions is to use this in conjunction with an anaconda environment or a venv to make sure that you separate the production blankly from your local source.

1. First [fork](https://help.github.com/articles/fork-a-repo/) the repo to your own GitHub and then [clone](https://help.github.com/articles/cloning-a-repository/) it locally.

2. Create a new branch that highlights what you plan on changing:
```bash
$ git checkout -b MY_BRANCH_NAME
```

4. Install testing dependencies
```bash
$ pip install pytest pytest_mock
```
5. Ensure that you have proper API keys on the various exchanges to run the test, or submit a PR, and we can run them.

Now you should be up and running and installed from source.

### Running the Tests

In the root blankly directory simply run
```bash
$ pytest
```
If no tests are found add an `__init__.py` file to the `tests` folder.

### Easy Contributions Right Now

- Testing out API endpoints
  - You can test out the endpoints we have provided and make sure everything works as intended. If there are some
    subtle flaws, just make a pull!
- Adding new exchanges
  - Try adding exchanges or new endpoints to the ones that we're missing. Adding price data from different trading
    services can be extremely useful for the community.
  - We're currently skipping over deposit, withdrawal and transfer endpoints because the vulnerabilities created
    for the software aren't currently clear. If you think you see a safe way to implement these, open a suggestion.


## Current Package Roadmap

Feel free to take one of the features that are in the works on our [package roadmap](https://blankly.notion.site/a07253df7aa540a881be77dc9934a7fb?v=a8f21c42ef43453bb5dbb471ec939912)