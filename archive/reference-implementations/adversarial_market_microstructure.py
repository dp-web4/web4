#!/usr/bin/env python3
"""
Adversarial Market Microstructure
==================================

Exchange simulator with order books, heterogeneous trader strategies,
front-running detection, wash trading analysis, and MEV extraction
in the context of ATP markets.

Session 21 — Track 4
"""

from __future__ import annotations
import hashlib
import math
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ─── Order Book Types ───────────────────────────────────────────────────────

class OrderSide(Enum):
    BID = auto()
    ASK = auto()


class OrderType(Enum):
    LIMIT = auto()
    MARKET = auto()
    STOP = auto()


class OrderStatus(Enum):
    PENDING = auto()
    PARTIAL = auto()
    FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()


@dataclass
class Order:
    """An order in the ATP exchange."""
    order_id: str
    trader_id: str
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: float
    filled: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    timestamp: float = 0.0
    trust_score: float = 0.5

    @property
    def remaining(self) -> float:
        return self.quantity - self.filled


@dataclass
class Trade:
    """An executed trade."""
    trade_id: str
    buyer_id: str
    seller_id: str
    price: float
    quantity: float
    timestamp: float
    buyer_order_id: str
    seller_order_id: str
    fee: float = 0.0


class OrderBook:
    """Price-time priority order book for ATP trading."""

    def __init__(self, fee_rate: float = 0.001):
        self.bids: List[Order] = []
        self.asks: List[Order] = []
        self.trades: List[Trade] = []
        self.fee_rate: float = fee_rate
        self._next_trade: int = 0
        self.total_volume: float = 0.0
        self.total_fees: float = 0.0

    def submit(self, order: Order) -> List[Trade]:
        new_trades = []
        if order.order_type == OrderType.MARKET:
            new_trades = self._match_market(order)
        elif order.order_type == OrderType.LIMIT:
            new_trades = self._match_limit(order)
            if order.remaining > 0:
                self._insert(order)
        self.trades.extend(new_trades)
        return new_trades

    def _match_market(self, order: Order) -> List[Trade]:
        trades = []
        book = self.asks if order.side == OrderSide.BID else self.bids
        while order.remaining > 0 and book:
            best = book[0]
            fill_qty = min(order.remaining, best.remaining)
            trade = self._execute(order, best, best.price, fill_qty)
            trades.append(trade)
            if best.remaining <= 0:
                book.pop(0)
        if order.remaining <= 0:
            order.status = OrderStatus.FILLED
        elif order.filled > 0:
            order.status = OrderStatus.PARTIAL
        return trades

    def _match_limit(self, order: Order) -> List[Trade]:
        trades = []
        if order.side == OrderSide.BID:
            while order.remaining > 0 and self.asks:
                best_ask = self.asks[0]
                if best_ask.price > order.price:
                    break
                fill_qty = min(order.remaining, best_ask.remaining)
                trade = self._execute(order, best_ask, best_ask.price, fill_qty)
                trades.append(trade)
                if best_ask.remaining <= 0:
                    self.asks.pop(0)
        else:
            while order.remaining > 0 and self.bids:
                best_bid = self.bids[0]
                if best_bid.price < order.price:
                    break
                fill_qty = min(order.remaining, best_bid.remaining)
                trade = self._execute(order, best_bid, best_bid.price, fill_qty)
                trades.append(trade)
                if best_bid.remaining <= 0:
                    self.bids.pop(0)
        if order.remaining <= 0:
            order.status = OrderStatus.FILLED
        elif order.filled > 0:
            order.status = OrderStatus.PARTIAL
        return trades

    def _execute(self, aggressor: Order, resting: Order,
                 price: float, qty: float) -> Trade:
        fee = qty * price * self.fee_rate
        self._next_trade += 1
        buyer = aggressor if aggressor.side == OrderSide.BID else resting
        seller = resting if aggressor.side == OrderSide.BID else aggressor
        aggressor.filled += qty
        resting.filled += qty
        if resting.remaining <= 0:
            resting.status = OrderStatus.FILLED
        self.total_volume += qty * price
        self.total_fees += fee
        return Trade(
            trade_id=f"T{self._next_trade}",
            buyer_id=buyer.trader_id, seller_id=seller.trader_id,
            price=price, quantity=qty,
            timestamp=max(aggressor.timestamp, resting.timestamp),
            buyer_order_id=buyer.order_id, seller_order_id=seller.order_id,
            fee=fee,
        )

    def _insert(self, order: Order):
        if order.side == OrderSide.BID:
            inserted = False
            for i, existing in enumerate(self.bids):
                if order.price > existing.price:
                    self.bids.insert(i, order)
                    inserted = True
                    break
            if not inserted:
                self.bids.append(order)
        else:
            inserted = False
            for i, existing in enumerate(self.asks):
                if order.price < existing.price:
                    self.asks.insert(i, order)
                    inserted = True
                    break
            if not inserted:
                self.asks.append(order)

    def cancel(self, order_id: str) -> bool:
        for book in [self.bids, self.asks]:
            for i, order in enumerate(book):
                if order.order_id == order_id:
                    order.status = OrderStatus.CANCELLED
                    book.pop(i)
                    return True
        return False

    def best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None

    def best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None

    def spread(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        if bb is not None and ba is not None:
            return ba - bb
        return None

    def mid_price(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        if bb is not None and ba is not None:
            return (bb + ba) / 2
        return None

    def depth(self, side: OrderSide, levels: int = 5) -> List[Tuple[float, float]]:
        book = self.bids if side == OrderSide.BID else self.asks
        result = []
        current_price = None
        current_qty = 0.0
        for order in book:
            if order.price != current_price:
                if current_price is not None:
                    result.append((current_price, current_qty))
                    if len(result) >= levels:
                        break
                current_price = order.price
                current_qty = order.remaining
            else:
                current_qty += order.remaining
        if current_price is not None and len(result) < levels:
            result.append((current_price, current_qty))
        return result

    def vwap(self, n_trades: int = 10) -> float:
        recent = self.trades[-n_trades:]
        if not recent:
            return 0.0
        total_value = sum(t.price * t.quantity for t in recent)
        total_qty = sum(t.quantity for t in recent)
        return total_value / max(total_qty, 1e-10)


# ─── Trader Strategies ─────────────────────────────────────────────────────

class TraderStrategy(Enum):
    MARKET_MAKER = auto()
    MOMENTUM = auto()
    MEAN_REVERSION = auto()
    RANDOM = auto()
    FRONT_RUNNER = auto()
    WASH_TRADER = auto()
    SANDWICH = auto()


@dataclass
class Trader:
    trader_id: str
    strategy: TraderStrategy
    balance_atp: float = 1000.0
    balance_token: float = 100.0
    trust_score: float = 0.5
    _order_count: int = 0
    _pnl: float = 0.0
    trades_executed: int = 0
    orders_submitted: int = 0

    def next_order_id(self) -> str:
        self._order_count += 1
        return f"{self.trader_id}_O{self._order_count}"


class MarketMakerStrategy:
    @staticmethod
    def generate_orders(trader: Trader, book: OrderBook,
                        now: float, rng: random.Random) -> List[Order]:
        mid = book.mid_price() or 100.0
        spread_half = mid * 0.005
        qty = min(10.0, trader.balance_atp * 0.05)
        orders = []
        if trader.balance_token > 0:
            orders.append(Order(
                order_id=trader.next_order_id(), trader_id=trader.trader_id,
                side=OrderSide.BID, order_type=OrderType.LIMIT,
                price=round(mid - spread_half, 4), quantity=qty,
                timestamp=now, trust_score=trader.trust_score))
        if trader.balance_atp > qty:
            orders.append(Order(
                order_id=trader.next_order_id(), trader_id=trader.trader_id,
                side=OrderSide.ASK, order_type=OrderType.LIMIT,
                price=round(mid + spread_half, 4), quantity=qty,
                timestamp=now, trust_score=trader.trust_score))
        return orders


class MomentumStrategy:
    @staticmethod
    def generate_orders(trader: Trader, book: OrderBook,
                        now: float, rng: random.Random) -> List[Order]:
        if len(book.trades) < 3:
            return []
        prices = [t.price for t in book.trades[-5:]]
        trend = prices[-1] - prices[0]
        qty = min(5.0, trader.balance_atp * 0.03)
        if trend > 0:
            return [Order(order_id=trader.next_order_id(),
                          trader_id=trader.trader_id,
                          side=OrderSide.BID, order_type=OrderType.MARKET,
                          price=0, quantity=qty, timestamp=now,
                          trust_score=trader.trust_score)]
        elif trend < 0:
            return [Order(order_id=trader.next_order_id(),
                          trader_id=trader.trader_id,
                          side=OrderSide.ASK, order_type=OrderType.MARKET,
                          price=0, quantity=qty, timestamp=now,
                          trust_score=trader.trust_score)]
        return []


class MeanReversionStrategy:
    @staticmethod
    def generate_orders(trader: Trader, book: OrderBook,
                        now: float, rng: random.Random) -> List[Order]:
        if len(book.trades) < 10:
            return []
        prices = [t.price for t in book.trades[-20:]]
        avg = sum(prices) / len(prices)
        current = prices[-1]
        deviation = (current - avg) / max(avg, 0.01)
        qty = min(5.0, trader.balance_atp * 0.03)
        if deviation > 0.002:
            return [Order(order_id=trader.next_order_id(),
                          trader_id=trader.trader_id,
                          side=OrderSide.ASK, order_type=OrderType.LIMIT,
                          price=round(current * 0.998, 4), quantity=qty,
                          timestamp=now, trust_score=trader.trust_score)]
        elif deviation < -0.002:
            return [Order(order_id=trader.next_order_id(),
                          trader_id=trader.trader_id,
                          side=OrderSide.BID, order_type=OrderType.LIMIT,
                          price=round(current * 1.002, 4), quantity=qty,
                          timestamp=now, trust_score=trader.trust_score)]
        return []


class RandomStrategy:
    @staticmethod
    def generate_orders(trader: Trader, book: OrderBook,
                        now: float, rng: random.Random) -> List[Order]:
        mid = book.mid_price() or 100.0
        side = OrderSide.BID if rng.random() > 0.5 else OrderSide.ASK
        price_offset = (rng.random() - 0.5) * mid * 0.02
        qty = min(rng.uniform(1, 8), trader.balance_atp * 0.05)
        return [Order(order_id=trader.next_order_id(),
                      trader_id=trader.trader_id,
                      side=side, order_type=OrderType.LIMIT,
                      price=round(mid + price_offset, 4),
                      quantity=round(qty, 2), timestamp=now,
                      trust_score=trader.trust_score)]


# ─── Adversarial Strategies ────────────────────────────────────────────────

class FrontRunnerStrategy:
    @staticmethod
    def detect_opportunity(book: OrderBook, pending: List[Order]) -> Optional[Order]:
        for order in pending:
            if order.quantity > 20:
                return order
        return None

    @staticmethod
    def generate_orders(trader: Trader, book: OrderBook,
                        now: float, rng: random.Random,
                        pending: Optional[List[Order]] = None) -> List[Order]:
        if not pending:
            return []
        target = FrontRunnerStrategy.detect_opportunity(book, pending)
        if not target:
            return []
        if target.side == OrderSide.BID:
            price = round((book.best_ask() or 100.0) - 0.01, 4)
        else:
            price = round((book.best_bid() or 100.0) + 0.01, 4)
        qty = min(5.0, trader.balance_atp * 0.1)
        return [Order(order_id=trader.next_order_id(),
                      trader_id=trader.trader_id,
                      side=target.side, order_type=OrderType.LIMIT,
                      price=price, quantity=qty,
                      timestamp=now - 0.001,
                      trust_score=trader.trust_score)]


class WashTraderStrategy:
    @staticmethod
    def generate_orders(trader: Trader, book: OrderBook,
                        now: float, rng: random.Random) -> List[Order]:
        mid = book.mid_price() or 100.0
        return [
            Order(order_id=trader.next_order_id(), trader_id=trader.trader_id,
                  side=OrderSide.BID, order_type=OrderType.LIMIT,
                  price=round(mid, 4), quantity=3.0,
                  timestamp=now, trust_score=trader.trust_score),
            Order(order_id=trader.next_order_id(), trader_id=trader.trader_id,
                  side=OrderSide.ASK, order_type=OrderType.LIMIT,
                  price=round(mid, 4), quantity=3.0,
                  timestamp=now + 0.001, trust_score=trader.trust_score),
        ]


class SandwichStrategy:
    @staticmethod
    def generate_orders(trader: Trader, book: OrderBook,
                        target: Order, now: float) -> Tuple[Order, Order]:
        front = Order(order_id=trader.next_order_id(),
                      trader_id=trader.trader_id,
                      side=OrderSide.BID, order_type=OrderType.MARKET,
                      price=0,
                      quantity=min(target.quantity * 0.5, trader.balance_atp * 0.1),
                      timestamp=now - 0.002, trust_score=trader.trust_score)
        back = Order(order_id=trader.next_order_id(),
                     trader_id=trader.trader_id,
                     side=OrderSide.ASK, order_type=OrderType.MARKET,
                     price=0, quantity=front.quantity,
                     timestamp=now + 0.002, trust_score=trader.trust_score)
        return front, back


# ─── Market Surveillance ───────────────────────────────────────────────────

@dataclass
class SurveillanceAlert:
    alert_type: str
    severity: float
    trader_id: str
    details: str
    timestamp: float


class MarketSurveillance:
    def __init__(self):
        self.alerts: List[SurveillanceAlert] = []
        self.trader_history: Dict[str, List[Trade]] = defaultdict(list)

    def record_trade(self, trade: Trade):
        self.trader_history[trade.buyer_id].append(trade)
        self.trader_history[trade.seller_id].append(trade)

    def detect_wash_trading(self, trades: List[Trade],
                            window: int = 20) -> List[SurveillanceAlert]:
        alerts = []
        recent = trades[-window:]
        for trade in recent:
            if trade.buyer_id == trade.seller_id:
                alerts.append(SurveillanceAlert(
                    "WASH_TRADE", 0.9, trade.buyer_id,
                    f"Self-trade: {trade.quantity}@{trade.price}",
                    trade.timestamp))

        flow_map: Dict[Tuple[str, str], float] = defaultdict(float)
        for trade in recent:
            flow_map[(trade.buyer_id, trade.seller_id)] += trade.quantity
        for (a, b), qty_ab in flow_map.items():
            qty_ba = flow_map.get((b, a), 0.0)
            if qty_ba > 0 and a != b:
                circular_ratio = min(qty_ab, qty_ba) / max(qty_ab, qty_ba)
                if circular_ratio > 0.8:
                    alerts.append(SurveillanceAlert(
                        "CIRCULAR_FLOW", circular_ratio, a,
                        f"Circular flow with {b}: ratio={circular_ratio:.2f}",
                        recent[-1].timestamp))
        self.alerts.extend(alerts)
        return alerts

    def detect_front_running(self, trades: List[Trade],
                             orders: List[Order],
                             window_ms: float = 100.0) -> List[SurveillanceAlert]:
        alerts = []
        sorted_orders = sorted(orders, key=lambda o: o.timestamp)
        for i in range(len(sorted_orders) - 1):
            curr = sorted_orders[i]
            next_order = sorted_orders[i + 1]
            if (next_order.timestamp - curr.timestamp < window_ms / 1000 and
                    curr.side == next_order.side and
                    curr.quantity < next_order.quantity * 0.3 and
                    curr.trader_id != next_order.trader_id and
                    next_order.quantity > 15):
                alerts.append(SurveillanceAlert(
                    "FRONT_RUNNING", 0.7, curr.trader_id,
                    f"Small order before large {next_order.trader_id} order",
                    curr.timestamp))
        self.alerts.extend(alerts)
        return alerts

    def detect_spoofing(self, book: OrderBook,
                        cancel_history: Dict[str, int],
                        threshold: float = 0.8) -> List[SurveillanceAlert]:
        alerts = []
        for trader_id, cancel_count in cancel_history.items():
            total = cancel_count + sum(
                1 for t in book.trades if
                t.buyer_id == trader_id or t.seller_id == trader_id)
            if total > 0:
                cancel_rate = cancel_count / total
                if cancel_rate > threshold and cancel_count > 5:
                    alerts.append(SurveillanceAlert(
                        "SPOOFING", cancel_rate, trader_id,
                        f"Cancel rate: {cancel_rate:.2%} ({cancel_count}/{total})",
                        time.time()))
        self.alerts.extend(alerts)
        return alerts

    def trust_weighted_severity(self, alert: SurveillanceAlert,
                                trust: float) -> float:
        trust_factor = 1.0 + (0.5 - trust)
        return min(1.0, alert.severity * trust_factor)


# ─── Market Metrics ────────────────────────────────────────────────────────

@dataclass
class MarketMetrics:
    total_volume: float = 0.0
    trade_count: int = 0
    avg_spread: float = 0.0
    volatility: float = 0.0
    wash_trade_pct: float = 0.0
    gini_coefficient: float = 0.0

    @staticmethod
    def compute(book: OrderBook, traders: List[Trader]) -> MarketMetrics:
        m = MarketMetrics()
        m.total_volume = book.total_volume
        m.trade_count = len(book.trades)
        if book.trades:
            prices = [t.price for t in book.trades]
            if len(prices) > 1:
                returns = [(prices[i] - prices[i-1]) / max(prices[i-1], 0.01)
                           for i in range(1, len(prices))]
                m.volatility = (sum(r*r for r in returns) / len(returns)) ** 0.5
        self_trades = sum(1 for t in book.trades if t.buyer_id == t.seller_id)
        m.wash_trade_pct = self_trades / max(len(book.trades), 1)
        balances = sorted([t.balance_atp for t in traders])
        n = len(balances)
        if n > 0 and sum(balances) > 0:
            total = sum(balances)
            cum = 0.0
            area = 0.0
            for i, b in enumerate(balances):
                cum += b
                area += cum / total - (i + 1) / n
            m.gini_coefficient = abs(2 * area / n)
        return m


# ─── MEV Analysis ──────────────────────────────────────────────────────────

@dataclass
class MEVOpportunity:
    mev_type: str
    expected_profit: float
    required_capital: float
    risk_score: float
    affected_traders: List[str]


class MEVAnalyzer:
    @staticmethod
    def find_arbitrage(book_a: OrderBook, book_b: OrderBook) -> Optional[MEVOpportunity]:
        ask_a = book_a.best_ask()
        bid_b = book_b.best_bid()
        ask_b = book_b.best_ask()
        bid_a = book_a.best_bid()
        if ask_a and bid_b and bid_b > ask_a:
            return MEVOpportunity("arbitrage", bid_b - ask_a, ask_a, 0.1, [])
        if ask_b and bid_a and bid_a > ask_b:
            return MEVOpportunity("arbitrage", bid_a - ask_b, ask_b, 0.1, [])
        return None

    @staticmethod
    def estimate_sandwich_profit(book: OrderBook, target: Order) -> Optional[MEVOpportunity]:
        if target.side != OrderSide.BID or target.order_type != OrderType.MARKET:
            return None
        if not book.asks:
            return None
        front_price = book.asks[0].price
        total_ask_qty = sum(o.remaining for o in book.asks[:5])
        if total_ask_qty < 1:
            return None
        impact = target.quantity / total_ask_qty * front_price * 0.01
        back_price = front_price + impact
        sandwich_qty = min(target.quantity * 0.3, 10.0)
        profit = (back_price - front_price) * sandwich_qty
        return MEVOpportunity("sandwich", profit, front_price * sandwich_qty,
                              0.8, [target.trader_id])


# ─── Exchange Simulation ───────────────────────────────────────────────────

class ExchangeSimulator:
    def __init__(self, seed: int = 42):
        self.book = OrderBook(fee_rate=0.001)
        self.traders: Dict[str, Trader] = {}
        self.surveillance = MarketSurveillance()
        self.rng = random.Random(seed)
        self.round_number: int = 0
        self.all_orders: List[Order] = []

    def add_trader(self, trader: Trader):
        self.traders[trader.trader_id] = trader

    def _generate_strategy_orders(self, trader: Trader, now: float) -> List[Order]:
        if trader.strategy == TraderStrategy.MARKET_MAKER:
            return MarketMakerStrategy.generate_orders(trader, self.book, now, self.rng)
        elif trader.strategy == TraderStrategy.MOMENTUM:
            return MomentumStrategy.generate_orders(trader, self.book, now, self.rng)
        elif trader.strategy == TraderStrategy.MEAN_REVERSION:
            return MeanReversionStrategy.generate_orders(trader, self.book, now, self.rng)
        elif trader.strategy == TraderStrategy.RANDOM:
            return RandomStrategy.generate_orders(trader, self.book, now, self.rng)
        elif trader.strategy == TraderStrategy.WASH_TRADER:
            return WashTraderStrategy.generate_orders(trader, self.book, now, self.rng)
        return []

    def run_round(self) -> int:
        self.round_number += 1
        now = time.time() + self.round_number
        trade_count = 0
        trader_list = list(self.traders.values())
        self.rng.shuffle(trader_list)
        for trader in trader_list:
            orders = self._generate_strategy_orders(trader, now)
            for order in orders:
                trader.orders_submitted += 1
                trades = self.book.submit(order)
                trade_count += len(trades)
                self.all_orders.append(order)
                for trade in trades:
                    self.surveillance.record_trade(trade)
                    buyer = self.traders.get(trade.buyer_id)
                    seller = self.traders.get(trade.seller_id)
                    if buyer:
                        buyer.trades_executed += 1
                    if seller:
                        seller.trades_executed += 1
        return trade_count

    def run_simulation(self, rounds: int) -> MarketMetrics:
        for _ in range(rounds):
            self.run_round()
        return MarketMetrics.compute(self.book, list(self.traders.values()))


# ─── Checks ─────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: Order Book Basics ────────────────────────────────────────────
    book = OrderBook(fee_rate=0.001)

    bid = Order("O1", "alice", OrderSide.BID, OrderType.LIMIT, 100.0, 10.0, timestamp=1.0)
    trades = book.submit(bid)
    checks.append(("s1_limit_bid_rests", len(trades) == 0 and len(book.bids) == 1))

    ask = Order("O2", "bob", OrderSide.ASK, OrderType.LIMIT, 105.0, 10.0, timestamp=2.0)
    trades = book.submit(ask)
    checks.append(("s1_ask_rests", len(trades) == 0 and len(book.asks) == 1))

    cross = Order("O3", "carol", OrderSide.ASK, OrderType.LIMIT, 99.0, 5.0, timestamp=3.0)
    trades = book.submit(cross)
    checks.append(("s1_cross_matches", len(trades) == 1 and
                    trades[0].price == 100.0 and trades[0].quantity == 5.0))

    checks.append(("s1_partial_fill", bid.filled == 5.0 and bid.remaining == 5.0))
    checks.append(("s1_best_bid", book.best_bid() == 100.0))
    checks.append(("s1_best_ask", book.best_ask() == 105.0))
    checks.append(("s1_spread", abs(book.spread() - 5.0) < 0.01))
    checks.append(("s1_mid_price", abs(book.mid_price() - 102.5) < 0.01))

    mkt = Order("O4", "dave", OrderSide.BID, OrderType.MARKET, 0, 3.0, timestamp=4.0)
    trades = book.submit(mkt)
    checks.append(("s1_market_order", len(trades) == 1 and trades[0].price == 105.0))
    checks.append(("s1_vwap", book.vwap() > 0))

    new_bid = Order("O5", "eve", OrderSide.BID, OrderType.LIMIT, 98.0, 10.0, timestamp=5.0)
    book.submit(new_bid)
    cancelled = book.cancel("O5")
    checks.append(("s1_cancel", cancelled and new_bid.status == OrderStatus.CANCELLED))
    checks.append(("s1_fees", book.total_fees > 0))
    checks.append(("s1_depth", len(book.depth(OrderSide.BID, levels=3)) >= 1))

    # ── S2: Trader Strategies ────────────────────────────────────────────
    rng = random.Random(42)
    strategy_book = OrderBook()
    for i in range(10):
        strategy_book.submit(Order(f"seed_b{i}", "seeder", OrderSide.BID,
                                    OrderType.LIMIT, 100 - i * 0.1, 5.0, timestamp=float(i)))
        strategy_book.submit(Order(f"seed_a{i}", "seeder", OrderSide.ASK,
                                    OrderType.LIMIT, 101 + i * 0.1, 5.0, timestamp=float(i)))
    for i in range(5):
        strategy_book.submit(Order(f"hist{i}", "hist", OrderSide.BID,
                                    OrderType.MARKET, 0, 2.0, timestamp=10.0 + i))

    mm = Trader("mm1", TraderStrategy.MARKET_MAKER, 1000, 100, 0.8)
    mm_orders = MarketMakerStrategy.generate_orders(mm, strategy_book, 20.0, rng)
    checks.append(("s2_mm_two_sided", len(mm_orders) == 2))
    if len(mm_orders) == 2:
        bid_p = next(o.price for o in mm_orders if o.side == OrderSide.BID)
        ask_p = next(o.price for o in mm_orders if o.side == OrderSide.ASK)
        checks.append(("s2_mm_spread", bid_p < ask_p))
    else:
        checks.append(("s2_mm_spread", False))

    mom = Trader("mom1", TraderStrategy.MOMENTUM, 1000, 100, 0.6)
    checks.append(("s2_momentum", len(MomentumStrategy.generate_orders(
        mom, strategy_book, 20.0, rng)) <= 1))

    rand = Trader("rand1", TraderStrategy.RANDOM, 1000, 100, 0.5)
    checks.append(("s2_random_generates", len(RandomStrategy.generate_orders(
        rand, strategy_book, 20.0, rng)) == 1))

    mr = Trader("mr1", TraderStrategy.MEAN_REVERSION, 1000, 100, 0.7)
    checks.append(("s2_mean_reversion", len(MeanReversionStrategy.generate_orders(
        mr, strategy_book, 20.0, rng)) <= 1))

    # ── S3: Adversarial Strategies ───────────────────────────────────────
    wt = Trader("wash1", TraderStrategy.WASH_TRADER, 1000, 100, 0.3)
    wt_orders = WashTraderStrategy.generate_orders(wt, strategy_book, 30.0, rng)
    checks.append(("s3_wash_two_orders", len(wt_orders) == 2))
    checks.append(("s3_wash_same_trader", len(wt_orders) == 2 and
                    wt_orders[0].trader_id == wt_orders[1].trader_id))

    large_order = Order("big1", "whale", OrderSide.BID, OrderType.MARKET, 0, 50.0, timestamp=40.0)
    checks.append(("s3_front_detect",
                    FrontRunnerStrategy.detect_opportunity(strategy_book, [large_order]) is not None))

    fr = Trader("front1", TraderStrategy.FRONT_RUNNER, 1000, 100, 0.2)
    fr_orders = FrontRunnerStrategy.generate_orders(fr, strategy_book, 40.0, rng, pending=[large_order])
    checks.append(("s3_front_order", len(fr_orders) == 1))
    checks.append(("s3_front_has_price", len(fr_orders) == 1 and fr_orders[0].price > 0))

    sw = Trader("sand1", TraderStrategy.SANDWICH, 1000, 100, 0.1)
    target_order = Order("target1", "victim", OrderSide.BID, OrderType.MARKET, 0, 30.0, timestamp=50.0)
    front, back = SandwichStrategy.generate_orders(sw, strategy_book, target_order, 50.0)
    checks.append(("s3_sandwich_pair", front.side == OrderSide.BID and back.side == OrderSide.ASK))
    checks.append(("s3_sandwich_timing", front.timestamp < target_order.timestamp < back.timestamp))

    # ── S4: Market Surveillance ──────────────────────────────────────────
    surv = MarketSurveillance()

    wash_trades = [
        Trade("T1", "wash1", "wash1", 100, 10, 1.0, "O1", "O2"),
        Trade("T2", "wash1", "wash1", 100, 10, 2.0, "O3", "O4"),
        Trade("T3", "alice", "bob", 100, 5, 3.0, "O5", "O6"),
    ]
    wash_alerts = surv.detect_wash_trading(wash_trades)
    checks.append(("s4_wash_detected",
                    len([a for a in wash_alerts if a.alert_type == "WASH_TRADE"]) == 2))

    circular_trades = [
        Trade("T1", "A", "B", 100, 10, 1.0, "O1", "O2"),
        Trade("T2", "B", "A", 100, 9, 2.0, "O3", "O4"),
    ]
    circular_alerts = surv.detect_wash_trading(circular_trades)
    checks.append(("s4_circular_detected",
                    len([a for a in circular_alerts if a.alert_type == "CIRCULAR_FLOW"]) >= 1))

    fr_orders_det = [
        Order("small1", "front_runner", OrderSide.BID, OrderType.LIMIT, 100, 2.0, timestamp=1.0),
        Order("big1", "whale", OrderSide.BID, OrderType.MARKET, 0, 50.0, timestamp=1.05),
    ]
    fr_alerts = surv.detect_front_running([], fr_orders_det)
    checks.append(("s4_frontrun_detected",
                    len([a for a in fr_alerts if a.alert_type == "FRONT_RUNNING"]) >= 1))

    cancel_hist = {"spoofer": 20, "honest": 1}
    spoof_book = OrderBook()
    spoof_book.trades = [
        Trade("T1", "spoofer", "x", 100, 1, 1.0, "O1", "O2"),
        Trade("T2", "honest", "y", 100, 10, 2.0, "O3", "O4"),
    ]
    spoof_alerts = surv.detect_spoofing(spoof_book, cancel_hist)
    checks.append(("s4_spoofing_detected",
                    len([a for a in spoof_alerts if a.alert_type == "SPOOFING"]) >= 1))

    low_trust_alert = SurveillanceAlert("WASH_TRADE", 0.5, "bad_actor", "test", 1.0)
    checks.append(("s4_trust_weighted",
                    surv.trust_weighted_severity(low_trust_alert, 0.1) >
                    surv.trust_weighted_severity(low_trust_alert, 0.9)))

    # ── S5: MEV Analysis ────────────────────────────────────────────────
    book_a = OrderBook()
    book_b = OrderBook()
    book_a.submit(Order("a1", "x", OrderSide.ASK, OrderType.LIMIT, 100.0, 10.0, timestamp=1.0))
    book_b.submit(Order("b1", "y", OrderSide.BID, OrderType.LIMIT, 105.0, 10.0, timestamp=1.0))
    arb = MEVAnalyzer.find_arbitrage(book_a, book_b)
    checks.append(("s5_arbitrage_found", arb is not None and arb.expected_profit == 5.0))

    book_c = OrderBook()
    book_d = OrderBook()
    book_c.submit(Order("c1", "x", OrderSide.ASK, OrderType.LIMIT, 100.0, 10.0, timestamp=1.0))
    book_d.submit(Order("d1", "y", OrderSide.BID, OrderType.LIMIT, 95.0, 10.0, timestamp=1.0))
    checks.append(("s5_no_arbitrage", MEVAnalyzer.find_arbitrage(book_c, book_d) is None))

    sand_book = OrderBook()
    for i in range(5):
        sand_book.submit(Order(f"sb{i}", "lp", OrderSide.ASK, OrderType.LIMIT,
                                100 + i, 10.0, timestamp=float(i)))
    tgt = Order("tgt", "victim", OrderSide.BID, OrderType.MARKET, 0, 20.0, timestamp=10.0)
    sand_mev = MEVAnalyzer.estimate_sandwich_profit(sand_book, tgt)
    checks.append(("s5_sandwich_profit", sand_mev is not None and sand_mev.expected_profit > 0))
    checks.append(("s5_sandwich_risk", sand_mev is not None and sand_mev.risk_score >= 0.8))

    # ── S6: Exchange Simulation ──────────────────────────────────────────
    sim = ExchangeSimulator(seed=42)
    sim.add_trader(Trader("mm1", TraderStrategy.MARKET_MAKER, 5000, 500, 0.9))
    sim.add_trader(Trader("mm2", TraderStrategy.MARKET_MAKER, 5000, 500, 0.85))
    sim.add_trader(Trader("mom1", TraderStrategy.MOMENTUM, 2000, 200, 0.7))
    sim.add_trader(Trader("mr1", TraderStrategy.MEAN_REVERSION, 2000, 200, 0.75))
    for i in range(6):
        sim.add_trader(Trader(f"rand{i}", TraderStrategy.RANDOM, 1000, 100, 0.5))
    sim.add_trader(Trader("wash1", TraderStrategy.WASH_TRADER, 1000, 100, 0.2))

    metrics = sim.run_simulation(50)
    checks.append(("s6_50_rounds", sim.round_number == 50))
    checks.append(("s6_trades_occurred", metrics.trade_count > 10))
    checks.append(("s6_volume", metrics.total_volume > 0))
    active_count = sum(1 for t in sim.traders.values() if t.orders_submitted > 0)
    # Strategy-gated traders (Momentum, MeanReversion) may be idle in stable markets
    checks.append(("s6_most_active", active_count >= len(sim.traders) - 2))

    wash_alerts_sim = sim.surveillance.detect_wash_trading(sim.book.trades)
    checks.append(("s6_wash_in_sim", any(a.alert_type == "WASH_TRADE" for a in wash_alerts_sim)))

    mm_trades = sum(t.trades_executed for t in sim.traders.values()
                    if t.strategy == TraderStrategy.MARKET_MAKER)
    checks.append(("s6_mm_active", mm_trades > 0))

    # ── S7: Market Metrics ───────────────────────────────────────────────
    checks.append(("s7_volatility", metrics.volatility >= 0))
    checks.append(("s7_wash_pct", 0 <= metrics.wash_trade_pct <= 1))
    checks.append(("s7_gini_bounded", 0 <= metrics.gini_coefficient <= 1))
    empty_metrics = MarketMetrics.compute(OrderBook(), [])
    checks.append(("s7_empty_metrics", empty_metrics.total_volume == 0 and empty_metrics.trade_count == 0))

    # ── S8: Order Book Depth ────────────────────────────────────────────
    deep_book = OrderBook()
    for i in range(20):
        deep_book.submit(Order(f"db{i}", f"t{i}", OrderSide.BID, OrderType.LIMIT,
                                100 - i * 0.5, float(10 + i), timestamp=float(i)))
        deep_book.submit(Order(f"da{i}", f"t{i}", OrderSide.ASK, OrderType.LIMIT,
                                101 + i * 0.5, float(10 + i), timestamp=float(i)))

    bid_depth = deep_book.depth(OrderSide.BID, levels=5)
    checks.append(("s8_bid_depth", len(bid_depth) == 5 and
                    all(bid_depth[i][0] >= bid_depth[i+1][0] for i in range(len(bid_depth) - 1))))
    ask_depth = deep_book.depth(OrderSide.ASK, levels=5)
    checks.append(("s8_ask_depth", len(ask_depth) == 5 and
                    all(ask_depth[i][0] <= ask_depth[i+1][0] for i in range(len(ask_depth) - 1))))
    checks.append(("s8_total_depth", sum(qty for _, qty in bid_depth) > 0))

    # ── S9: Trust-Gated Trading ──────────────────────────────────────────
    surv2 = MarketSurveillance()
    checks.append(("s9_trust_gating",
                    surv2.trust_weighted_severity(SurveillanceAlert("T", 0.5, "a", "", 0), 0.1) >
                    surv2.trust_weighted_severity(SurveillanceAlert("T", 0.5, "b", "", 0), 0.9)))
    checks.append(("s9_perfect_trust",
                    surv2.trust_weighted_severity(SurveillanceAlert("T", 0.5, "c", "", 0), 1.0) < 0.5))
    checks.append(("s9_zero_trust",
                    surv2.trust_weighted_severity(SurveillanceAlert("T", 0.5, "d", "", 0), 0.0) > 0.5))

    # ── S10: Market Integrity ────────────────────────────────────────────
    checks.append(("s10_fees_positive", sim.book.total_fees >= 0))
    checks.append(("s10_valid_prices", all(t.price > 0 for t in sim.book.trades)))
    checks.append(("s10_valid_qty", all(t.quantity > 0 for t in sim.book.trades)))
    trade_ids = [t.trade_id for t in sim.book.trades]
    checks.append(("s10_unique_trades", len(trade_ids) == len(set(trade_ids))))

    # ── S11: Performance ─────────────────────────────────────────────────
    big_sim = ExchangeSimulator(seed=123)
    for i in range(10):
        big_sim.add_trader(Trader(f"mm_{i}", TraderStrategy.MARKET_MAKER, 5000, 500, 0.8))
    for i in range(5):
        big_sim.add_trader(Trader(f"rnd_{i}", TraderStrategy.RANDOM, 1000, 100, 0.5))
    for i in range(3):
        big_sim.add_trader(Trader(f"mom_{i}", TraderStrategy.MOMENTUM, 2000, 200, 0.6))
    big_sim.add_trader(Trader("mr_0", TraderStrategy.MEAN_REVERSION, 2000, 200, 0.7))
    big_sim.add_trader(Trader("wash_0", TraderStrategy.WASH_TRADER, 1000, 100, 0.2))

    t_start = time.time()
    big_metrics = big_sim.run_simulation(200)
    checks.append(("s11_200_rounds", time.time() - t_start < 5.0))
    checks.append(("s11_volume", big_metrics.trade_count > 100))

    t_start = time.time()
    big_sim.surveillance.detect_wash_trading(big_sim.book.trades, window=100)
    checks.append(("s11_surveillance", time.time() - t_start < 2.0))

    # ── Report ───────────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    elapsed = time.time() - t0

    print("=" * 60)
    print(f"  Adversarial Market Microstructure — {passed}/{total} checks passed")
    print("=" * 60)
    failures = []
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            failures.append(name)
    if failures:
        print(f"\n  FAILURES:")
        for f in failures:
            print(f"    ✗ {f}")
    print(f"\n  Time: {elapsed:.2f}s")
    return passed == total


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)
