# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://mango.markets/) support is available at:
#   [Docs](https://docs.mango.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)


import logging
import typing
import websocket

from rx.core.typing import Disposable
from solana.publickey import PublicKey
from solana.rpc.types import RPCResponse

from .accountinfo import AccountInfo
from .context import Context
from .observables import EventSource


# # 🥭 WebSocketSubscription class
#
# The `WebSocketSubscription` maintains a mapping for an account subscription in a Solana websocket to
# an actual instantiated object.
#


TSubscriptionInstance = typing.TypeVar('TSubscriptionInstance')


class WebSocketSubscription(Disposable, typing.Generic[TSubscriptionInstance]):
    def __init__(self, context: Context, address: PublicKey, constructor: typing.Callable[[AccountInfo], TSubscriptionInstance]):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.address = address
        self.id = context.random_client_id()
        self.subscription_id = 0
        self.from_account_info: typing.Callable[[AccountInfo], TSubscriptionInstance] = constructor
        self.publisher: EventSource[TSubscriptionInstance] = EventSource[TSubscriptionInstance]()

    def build_request(self) -> str:
        return """
{
    "jsonrpc": "2.0",
    "id": \"""" + str(self.id) + """\",
    "method": "accountSubscribe",
    "params": [\"""" + str(self.address) + """\",
        {
            "encoding": "base64",
            "commitment": "processed"
        }
    ]
}
"""

    def build_account_info(self, response: RPCResponse) -> AccountInfo:
        return AccountInfo.from_response(response, self.address)

    def build(self, response: RPCResponse) -> TSubscriptionInstance:
        account_info: AccountInfo = self.build_account_info(response)
        built: TSubscriptionInstance = self.from_account_info(account_info)
        return built

    def dispose(self):
        self.publisher.on_completed()
        self.publisher.dispose()


# # 🥭 WebSocketSubscriptionManager class
#
# The `WebSocketSubscriptionManager` takes websocket account updates and sends them to the correct
# `WebSocketSubscription`.
#


class WebSocketSubscriptionManager(Disposable):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.subscriptions: typing.List[WebSocketSubscription] = []

    def add(self, subscription: WebSocketSubscription) -> None:
        self.subscriptions += [subscription]

    def add_subscription_id(self, id, subscription_id) -> None:
        for subscription in self.subscriptions:
            if subscription.id == id:
                self.logger.info(
                    f"Setting ID {subscription_id} on subscription {subscription.address}/{subscription.id}.")
                subscription.subscription_id = subscription_id
                return
        self.logger.error(f"Subscription ID {id} not found")

    def subscription_by_subscription_id(self, subscription_id) -> WebSocketSubscription:
        for subscription in self.subscriptions:
            if subscription.subscription_id == subscription_id:
                return subscription
        raise Exception(f"No subscription with subscription ID {subscription_id} could be found.")

    def on_item(self, response) -> None:
        if "method" not in response:
            id: int = int(response["id"])
            subscription_id: int = int(response["result"])
            self.add_subscription_id(id, subscription_id)
        elif response["method"] == "accountNotification":
            subscription_id = response["params"]["subscription"]
            subscription = self.subscription_by_subscription_id(subscription_id)
            built = subscription.build(response["params"])
            subscription.publisher.publish(built)
        else:
            self.logger.error(f"Unknown response: {response}")

    def open_handler(self, ws: websocket.WebSocketApp):
        for subscription in self.subscriptions:
            ws.send(subscription.build_request())

    def dispose(self):
        for subscription in self.subscriptions:
            subscription.dispose()