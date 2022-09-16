# TON Vanity Contract

Smart contract that allows to "mine" any suitable address for any contract. One of the nice side-effects is that you can also use it as a primary deployment method for your contracts since you are specifying data and code as is and there are no need to have an alternative way init contract.

* 🔐 Secure. Address allocation binded to the wallet you control.
* 🚀 Fast. Suffix with few letters takes only few seconds.
* 🤝 Convenient. Vanity Contract is a simple way to deploy contracts and allows avoid implementing separate deployment logic.

## How it works

Creating a vanity address is a two step process:

1) "Mine" an addres with a our python tool. You can mine 5 letter suffix in seconds.
2) Deploy your contract code and data using special vanity message


## Mining Address

Checkout this repository on your machine with `Python 3.9` installed. It is recommended to use some computer with good GPU.

Execute in `src/generator` and replace `<suffix>` with desired suffix name and `<owner>` with an address of a wallet that then could be used for deployment.

```bash
python3.9 run.py --end <suffix> -w -1 --case-sensitive <owner>
```

Example output:
```bash
...
Found:  Ef_q7x1ZcJMZcWhanI6-t3giwAHOo6iX2YgovTvk0GryCLUB salt:  04fd8dda6b23067c1aa45c5af500174dc6c4d79b7d50c9de81ffb9e4a62c2d2a
Found:  Ef9Qa5dP5Y4E6xBURdBBF8_P8XMTdLJaQLGkoUA5Eya2CLUB salt:  b0181470628ea0c341c4327e188dfba1a46be8527933f031ef61af6f35ffacf8
...
```

Store this salt and an address somwhere for future deployment.

## License

MIT
