from abc import ABC, abstractmethod


# 1. 组件接口
class Coffee(ABC):
    @abstractmethod
    def cost(self) -> float:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


# 2. 具体组件 - 基础咖啡
class SimpleCoffee(Coffee):
    def cost(self) -> float:
        return 2.0

    def description(self) -> str:
        return "Simple coffee"


# 3. 装饰器基类
class CoffeeDecorator(Coffee):
    def __init__(self, coffee: Coffee):
        self._coffee = coffee

    def cost(self) -> float:
        return self._coffee.cost()

    def description(self) -> str:
        return self._coffee.description()


# 4. 具体装饰器
class MilkDecorator(CoffeeDecorator):
    def cost(self) -> float:
        return self._coffee.cost() + 0.5

    def description(self) -> str:
        return self._coffee.description() + ", milk"


class SugarDecorator(CoffeeDecorator):
    def cost(self) -> float:
        return self._coffee.cost() + 0.2

    def description(self) -> str:
        return self._coffee.description() + ", sugar"


class WhipDecorator(CoffeeDecorator):
    def cost(self) -> float:
        return self._coffee.cost() + 0.7

    def description(self) -> str:
        return self._coffee.description() + ", whip"


# 使用示例
def main():
    # 基础咖啡
    coffee = SimpleCoffee()
    print(f"{coffee.description()}: ${coffee.cost()}")

    # 加牛奶
    coffee_with_milk = MilkDecorator(coffee)
    print(f"{coffee_with_milk.description()}: ${coffee_with_milk.cost()}")

    # 加牛奶和糖
    coffee_with_milk_sugar = SugarDecorator(coffee_with_milk)
    print(f"{coffee_with_milk_sugar.description()}: ${coffee_with_milk_sugar.cost()}")

    # 加牛奶、糖和奶泡
    fancy_coffee = WhipDecorator(coffee_with_milk_sugar)
    print(f"{fancy_coffee.description()}: ${fancy_coffee.cost()}")


if __name__ == "__main__":
    main()
