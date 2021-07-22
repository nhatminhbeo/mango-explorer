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


import abc
import logging
import typing

from decimal import Decimal

from .constants import SYSTEM_PROGRAM_ADDRESS
from .orders import Order, OrderType, Side


# # 🥭 MarketOperations
#
# This file deals with placing orders. We want the interface to be simple and basic:
# ```
# order_placer.cancel_order(context, market)
# order_placer.place_order(context, market, side, order_type, price, quantity)
# ```
# This requires the `MarketOperations` already know a bit about the market it is placing the
# order on, and the code in the `MarketOperations` be specialised for that market platform.
#

# # 🥭 MarketOperations class
#
# This abstracts the process of placing orders, providing a base class for specialised operations.
#
# It's abstracted because we may want to have different approaches to placing these
# orders - do we want to run them against the Serum orderbook? Do we want to run them against
# Mango groups?
#
# Whichever choice is made, the calling code shouldn't have to care. It should be able to
# use its `MarketOperations` class as simply as:
# ```
# order_placer.place_order(context, side, order_type, price, quantity)
# ```
#


class MarketOperations(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def cancel_order(self, order: Order) -> typing.Sequence[str]:
        raise NotImplementedError("MarketOperations.cancel_order() is not implemented on the base type.")

    @abc.abstractmethod
    def place_order(self, side: Side, order_type: OrderType, price: Decimal, quantity: Decimal) -> Order:
        raise NotImplementedError("MarketOperations.place_order() is not implemented on the base type.")

    @abc.abstractmethod
    def load_orders(self) -> typing.Sequence[Order]:
        raise NotImplementedError("MarketOperations.load_orders() is not implemented on the base type.")

    @abc.abstractmethod
    def load_my_orders(self) -> typing.Sequence[Order]:
        raise NotImplementedError("MarketOperations.load_my_orders() is not implemented on the base type.")

    @abc.abstractmethod
    def settle(self) -> typing.Sequence[str]:
        raise NotImplementedError("MarketOperations.settle() is not implemented on the base type.")

    @abc.abstractmethod
    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        raise NotImplementedError("MarketOperations.crank() is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NullMarketOperations class
#
# A null, no-op, dry-run trade executor that can be plugged in anywhere a `MarketOperations`
# is expected, but which will not actually trade.
#

class NullMarketOperations(MarketOperations):
    def __init__(self, market_name: str):
        super().__init__()
        self.market_name: str = market_name

    def cancel_order(self, order: Order) -> typing.Sequence[str]:
        self.logger.info(
            f"Cancelling order {order.id} for quantity {order.quantity} at price {order.price} on market {self.market_name} with client ID {order.client_id}.")
        return [""]

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, quantity: Decimal) -> Order:
        self.logger.info(
            f"Placing {order_type} {side} order for quantity {quantity} at price {price} on market {self.market_name}.")
        return Order(id=0, side=side, price=price, quantity=quantity, client_id=0, owner=SYSTEM_PROGRAM_ADDRESS, order_type=order_type)

    def load_orders(self) -> typing.Sequence[Order]:
        return []

    def load_my_orders(self) -> typing.Sequence[Order]:
        return []

    def settle(self) -> typing.Sequence[str]:
        return []

    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        return []

    def __str__(self) -> str:
        return f"""« 𝙽𝚞𝚕𝚕𝙾𝚛𝚍𝚎𝚛𝙿𝚕𝚊𝚌𝚎𝚛 [{self.market_name}] »"""