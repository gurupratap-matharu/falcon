from django.test import TestCase

from orders.factories import OrderFactory, OrderItemFactory, PassengerFactory
from orders.models import Order, OrderItem, Passenger


class OrderModelTests(TestCase):
    """Test suite for the Order Model"""

    def setUp(self) -> None:
        self.order = OrderFactory()

    def test_str_representation(self):
        self.assertEqual(str(self.order), f"Order {self.order.id}")  # type: ignore

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.order._meta.verbose_name_plural), "orders")

    def test_order_model_creation_is_accurate(self):
        order_from_db = Order.objects.first()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order_from_db.name, self.order.name)
        self.assertEqual(order_from_db.email, self.order.email)
        self.assertEqual(order_from_db.residence, self.order.residence)
        self.assertEqual(order_from_db.paid, self.order.paid)

    def test_order_name_max_length(self):
        order = Order.objects.first()
        max_length = order._meta.get_field("name").max_length  # type:ignore

        self.assertEqual(max_length, 50)

    def test_new_order_is_always_unpaid(self):
        order = Order.objects.create(
            name="princy", email="princy@email.com", residence="IN"
        )

        self.assertFalse(order.paid)

    def test_same_payer_can_create_multiple_orders(self):
        Order.objects.all().delete()

        o_1 = OrderFactory(name="princy", email="princy@email.com", residence="IN")
        o_2 = OrderFactory(name="princy", email="princy@email.com", residence="IN")

        orders = Order.objects.all()

        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].name, o_1.name)
        self.assertEqual(orders[1].name, o_2.name)

    def test_orders_are_ordered_by_created_date(self):
        Order.objects.all().delete()

        o_1 = OrderFactory()
        o_2 = OrderFactory()
        o_3 = OrderFactory()

        orders = Order.objects.all()

        self.assertEqual(orders[0], o_3)
        self.assertEqual(orders[1], o_2)
        self.assertEqual(orders[2], o_1)

        order = orders[0]
        ordering = order._meta.ordering[0]  # type:ignore

        self.assertEqual(ordering, "-created_on")


class OrderItemModelTests(TestCase):
    """Test suite for the OrderItem Model"""

    pass


class PassengerModelTests(TestCase):
    """Test suite for the Passenger Model"""

    pass
