from sqlalchemy import Column, String, Float, Integer
from model.BaseEntity import BaseEntity


class FoodData(BaseEntity):
    """
    食物数据
    """
    __tablename__ = 'food_data'

    # 用户ID
    user_id = Column(Integer, nullable=False, comment="用户ID")

    # 设备ID
    device_id = Column(String(50), nullable=False, comment="设备ID")

    # 食物名称
    food_name = Column(String(255), nullable=True, comment="食物名称")

    # 食物图片URL
    food_image_url = Column(String(255), nullable=True, comment="食物图片URL")

    # 卡路里
    calories = Column(Float, nullable=True, comment="卡路里")

    # 蛋白质
    protein = Column(Float, nullable=True, comment="蛋白质")

    # 脂肪
    fat = Column(Float, nullable=True, comment="脂肪")

    # 碳水化合物含量
    carbohydrates = Column(Float, nullable=True, comment="碳水化合物含量")

    # 摄入的重量
    intake_food_weight = Column(Float, nullable=True, comment="摄入的重量")

    # 食物初始重量
    food_weight = Column(Float, nullable=True, comment="食物初始重量")

    # 进餐状态
    status = Column(Integer, nullable=True, comment="0:表示本次进餐还没有结束，1:表示本次进餐结束")

    def __repr__(self):
        return f"<FoodData(id={self.id}, food_name='{self.food_name}', calories={self.calories}, food_weight={self.food_weight})>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'food_name': self.food_name,
            'food_image_url': self.food_image_url,
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbohydrates': self.carbohydrates,
            'intake_food_weight': self.intake_food_weight,
            'food_weight': self.food_weight,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'create_by': self.create_by,
            'version': self.version,
            'del_flag': self.del_flag,
            'remark': self.remark
        }

    @property
    def actual_nutrition(self):
        if (
                self.intake_food_weight is not None
                and self.food_weight is not None
                and self.food_weight > 0
        ):
            ratio = self.intake_food_weight / self.food_weight
            return {
                "actual_calories": round(self.calories * ratio, 2) if self.calories else 0,
                "actual_protein": round(self.protein * ratio, 2) if self.protein else 0,
                "actual_fat": round(self.fat * ratio, 2) if self.fat else 0,
                "actual_carbohydrates": round(self.carbohydrates * ratio, 2) if self.carbohydrates else 0,
                "intake_ratio": round(ratio * 100, 2)
            }

        # ✅ 永不返回 None
        return {
            "actual_calories": 0,
            "actual_protein": 0,
            "actual_fat": 0,
            "actual_carbohydrates": 0,
            "intake_ratio": 0
        }


    def calculate_nutrition_per_100g(self):
        """计算每100g的营养成分"""
        if self.food_weight is None or self.food_weight <= 0:
            return 0

        ratio = 100 / self.food_weight
        return {
            "calories_per_100g": round(self.calories * ratio, 2) if self.calories else None,
            "protein_per_100g": round(self.protein * ratio, 2) if self.protein else None,
            "fat_per_100g": round(self.fat * ratio, 2) if self.fat else None,
            "carbohydrates_per_100g": round(self.carbohydrates * ratio, 2) if self.carbohydrates else None
        }


async def main():
    food_data = FoodData(calories=100, protein=10, fat=5, carbohydrates=20, food_weight=100, intake_food_weight=50)
    print(food_data.to_dict())
    print(food_data.calculate_nutrition_per_100g())
    print(food_data.actual_nutrition)
    res = food_data.actual_nutrition
    print(res["actual_calories"])

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
