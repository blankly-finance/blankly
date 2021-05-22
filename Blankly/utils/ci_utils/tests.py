import Blankly


if __name__ == "__main__":
    print("Hello world")

    interface = Blankly.Coinbase_Pro().get_interface()

    print(interface.get_fees())
