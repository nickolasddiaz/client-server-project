import pickle
from functools import partialmethod

from type import Command, ResponseCode, KeyData


class Encoder:
    @staticmethod
    def encode(dict_items: dict, command: Command|ResponseCode) -> bytes:

        # overload a function both Enums Command and ResponseCode have a .value
        dict_items[KeyData.CMD] = command.value # set the key KeyData.CMD to an integer representing an enum

        return pickle.dumps(dict_items)

    @staticmethod
    def _decode(encoded_items: bytes, is_server : bool) -> dict:
        dict_items: dict = pickle.loads(encoded_items)
        if is_server:
            dict_items[KeyData.CMD] = ResponseCode(dict_items[KeyData.CMD]) # casting an int into an enum
        else:
            dict_items[KeyData.CMD] = Command(dict_items[KeyData.CMD])

        return dict_items

    # partial methods from the original private _decode function
    server_decode = partialmethod(_decode, is_server=True)
    client_decode = partialmethod(_decode, is_server=False)


if __name__ == "__main__":
    # create a dictionary
    items: dict = {"message": "Delete a file", "arg1": "testing", "arg2": 12345}
    encoder = Encoder()
    # pass the dictionary and the command to be decoded
    encoded_items: bytes = encoder.encode(items, Command.DELETE)

    print("encoded_items:\n", encoded_items)

    # pass the encoded message into the decoder
    decoded_items: dict = Encoder.client_decode(encoded_items)

    print("\ndecoded_items:\n")
    for key, value in decoded_items.items():
        print(f"{key}: {value}")

    command: Command = decoded_items[KeyData.CMD]
    print("\nPrinting the command that was used")
    print(f"command name: {command.name}, command description: {command.desc}")
