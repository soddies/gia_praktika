from django.db import models
from django.core.validators import MinValueValidator

class Unit(models.Model):
    unit_id = models.AutoField(primary_key=True)
    unit_name = models.CharField(max_length=20, db_column='unit_name')

    class Meta:
        db_table = 'units'
        managed = False

    def __str__(self):
        return self.unit_name

class Manufacturer(models.Model):
    manufacturer_id = models.AutoField(primary_key=True)
    manufacturer_name = models.CharField(max_length=200, db_column='manufacturer_name')

    class Meta:
        db_table = 'manufacturers'
        managed = False

    def __str__(self):
        return self.manufacturer_name

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=200, db_column='category_name')

    class Meta:
        db_table = 'categories'
        managed = False

    def __str__(self):
        return self.category_name

class Suppliers(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    supplier_name = models.CharField(max_length=200, db_column='supplier_name')

    class Meta:
        db_table = 'suppliers'
        managed = False

    def __str__(self):
        return self.supplier_name

class Roles(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100, db_column='role_name')

    class Meta:
        db_table = 'roles'
        managed = False

    def __str__(self):
        return self.role_name

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    role_id = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='role_id')
    full_name = models.CharField(max_length=500, db_column='full_name')
    login = models.CharField(max_length=100, db_column='login')
    password = models.CharField(max_length=60, db_column='password')

    class Meta:
        db_table = 'users'
        managed = False

    def __str__(self):
        return self.full_name

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    article = models.CharField(max_length=100, db_column='article')
    product_name = models.CharField(max_length=500, db_column='product_name')
    unit_id = models.ForeignKey(Unit, on_delete=models.CASCADE, db_column='unit_id')
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column='price', validators=[MinValueValidator(0)])
    supplier_id = models.ForeignKey(Suppliers, on_delete=models.CASCADE, db_column='supplier_id')
    manufacturer_id = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, db_column='manufacturer_id')
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id')
    discount = models.IntegerField(db_column='discount')
    stock_quantity = models.IntegerField(db_column='stock_quantity', validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, null=True, db_column='description')
    image_path = models.CharField(max_length=100, db_column='image_path')

    class Meta:
        db_table = 'products'
        managed = False

    def __str__(self):
        return self.product_name

class PickUpPoint(models.Model):
    pickuppoint_id = models.AutoField(primary_key=True)
    index = models.CharField(max_length=20, db_column='index')
    city = models.CharField(max_length=100, db_column='city')
    street = models.CharField(max_length=100, db_column='street')
    house = models.CharField(max_length=10, db_column='house')

    class Meta:
        db_table = 'pickuppoints'
        managed = False

    def __str__(self):
        return f"{self.city}, {self.street}, {self.house}"

class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    order_date = models.DateField(db_column='order_date')
    delivery_date = models.DateField(db_column='delivery_date')
    pickuppoint_id = models.ForeignKey(PickUpPoint, on_delete=models.CASCADE, db_column='pickuppoint_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    code = models.CharField(max_length=5, db_column='code')
    status = models.CharField(max_length=50, db_column='status')

    class Meta:
        db_table = 'orders'
        managed = False

    def __str__(self):
        return f"Заказ №{self.order_id}"

class Order_Item(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Orders, on_delete=models.CASCADE, db_column='order_id')
    product_id = models.ForeignKey(Product, on_delete=models.PROTECT, db_column='product_id')
    quantity = models.IntegerField(db_column='quantity')

    class Meta:
        db_table = 'order_item'
        managed = False

    def __str__(self):
        return f"{self.product_id.article} x {self.quantity}"

# Create your models here.
