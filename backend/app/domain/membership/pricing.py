"""Price of a membership: the tariff price wrapped by any number of paid options."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from app.domain.models import MembershipOption, TariffPlan


@dataclass(frozen=True)
class PriceLine:
    name: str
    amount: Decimal


class PriceComponent(ABC):
    """GoF: Decorator — Component: anything that has a price and can explain it line by line."""

    @abstractmethod
    def price(self) -> Decimal: ...

    @abstractmethod
    def lines(self) -> list[PriceLine]: ...


class TariffPrice(PriceComponent):
    """GoF: Decorator — ConcreteComponent: the base price of the tariff plan."""

    def __init__(self, tariff: TariffPlan) -> None:
        self.tariff = tariff

    def price(self) -> Decimal:
        return self.tariff.price

    def lines(self) -> list[PriceLine]:
        return [PriceLine(f"Тариф «{self.tariff.name}»", self.tariff.price)]


class PriceDecorator(PriceComponent):
    """GoF: Decorator — Decorator: keeps the wrapped component and delegates to it."""

    def __init__(self, wrapped: PriceComponent) -> None:
        self.wrapped = wrapped

    def price(self) -> Decimal:
        return self.wrapped.price()

    def lines(self) -> list[PriceLine]:
        return self.wrapped.lines()


class OptionDecorator(PriceDecorator):
    """GoF: Decorator — ConcreteDecorator: adds the cost of one paid option (sauna, locker, ...)."""

    def __init__(self, wrapped: PriceComponent, option: MembershipOption) -> None:
        super().__init__(wrapped)
        self.option = option

    def price(self) -> Decimal:
        return super().price() + self.option.price

    def lines(self) -> list[PriceLine]:
        return [*super().lines(), PriceLine(f"Опція «{self.option.name}»", self.option.price)]


def build_price(tariff: TariffPlan, options: Iterable[MembershipOption]) -> PriceComponent:
    """Wraps the tariff price in one decorator per selected option."""
    component: PriceComponent = TariffPrice(tariff)
    for option in options:
        component = OptionDecorator(component, option)
    return component
