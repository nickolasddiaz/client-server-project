import pickle
from type import Command, ResCode, KeyData


class Encoder:
    @staticmethod
    def encode(dict_items: dict, cmd: Command | ResCode) -> bytes:
        dict_items[KeyData.CMD] = cmd
        return pickle.dumps(dict_items)

    @staticmethod
    def decode(en_items) -> dict:
        dict_items: dict = pickle.loads(en_items)
        return dict_items


if __name__ == "__main__":
    # create a dictionary
    items: dict = {"message": "Delete a file", "arg1": "testing", "arg2": 12345}
    encoder = Encoder()
    # pass the dictionary and the cmd to be decoded
    encoded_items: bytes = encoder.encode(items, Command.DELETE)

    print("en_items:\n", encoded_items)

    # pass the encoded message into the decoder
    decoded_items: dict = Encoder.decode(encoded_items)

    print("\ndecoded_items:\n")
    for key, value in decoded_items.items():
        print(f"{key}: {value}")

    command: Command = decoded_items[KeyData.CMD]
    print("\nPrinting the cmd that was used")
    print(f"cmd name: {command.name}, cmd description: {command.desc}")
