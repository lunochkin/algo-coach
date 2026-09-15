"""`python -m algo_coach.broker`: the broker, on the network only the API shares
with it."""

import uvicorn

from algo_coach.broker.app import create_app

# the port the API calls the broker on, published nowhere
PORT = 8001


def main() -> None:
    # every interface of the broker's own container: the compose network
    # decides who reaches it
    uvicorn.run(create_app(), host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
