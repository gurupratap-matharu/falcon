import uuid


def mock_token():
    return str(uuid.uuid4())


class ModoMock:
    def __init__(self, order):
        print("mock payment intent called 🔥")
        pass

    def json(self):
        return {
            "id": str(uuid.uuid4()),
            "qr": "https:://qr.abc.modo.com",
            "deeplink": "https://modo.deeplink.com",
        }
