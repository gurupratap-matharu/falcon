from django.core.exceptions import ValidationError
from django.test import TestCase

from orders.factories import OrderFactory, OrderItemFactory, PassengerFactory
from orders.models import Order, OrderItem, Passenger
from trips.factories import TripFactory


class OrderModelTests(TestCase):
    """Test suite for the Order Model"""

    def setUp(self) -> None:
        self.passengers = PassengerFactory.create_batch(size=3)
        self.order = OrderFactory(passengers=self.passengers)

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
        self.assertEqual(order_from_db.passengers.count(), len(self.passengers))

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

    def test_order_total_cost_is_correct(self):
        order = Order.objects.first()

        order_item_1 = OrderItemFactory(order=order)
        order_item_2 = OrderItemFactory(order=order)

        expected = order_item_1.get_cost() + order_item_2.get_cost()
        actual = order.get_total_cost()

        self.assertEqual(actual, expected)


class OrderItemModelTests(TestCase):
    """Test suite for the OrderItem Model"""

    def setUp(self):
        self.trip = TripFactory()
        self.passengers = PassengerFactory.create_batch(size=2)
        self.order = OrderFactory(passengers=self.passengers)
        self.order_item = OrderItemFactory(order=self.order, trip=self.trip)

    def test_string_representation(self):
        self.assertEqual(
            str(self.order_item), f"OrderItem {self.order_item.id}"  # type:ignore
        )

    def test_verbose_name_plural(self):
        self.assertEqual(
            str(self.order_item._meta.verbose_name_plural), "order items"
        )  # type:ignore

    def test_order_item_model_creation_is_correct(self):
        order_item = OrderItem.objects.first()

        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(order_item.trip, self.order_item.trip)
        self.assertEqual(order_item.order, self.order_item.order)
        self.assertEqual(order_item.price, self.order_item.price)
        self.assertEqual(order_item.quantity, self.order_item.quantity)

    def test_order_item_cost_is_correctly_calculated(self):
        order_item = OrderItem.objects.first()

        actual_cost = order_item.get_cost()
        expected_cost = order_item.price * order_item.quantity

        self.assertEqual(actual_cost, expected_cost)

    def test_order_item_min_quantity(self):
        order_item = OrderItemFactory(order=self.order, trip=self.trip, quantity=0)

        with self.assertRaises(ValidationError):
            order_item.full_clean()

    def test_order_item_max_quantity(self):
        order_item = OrderItemFactory(order=self.order, trip=self.trip, quantity=10)

        with self.assertRaises(ValidationError):
            order_item.full_clean()


class PassengerModelTests(TestCase):
    """Test suite for the Passenger Model"""

    def setUp(self):
        self.trip = TripFactory()
        self.p1, self.p2 = PassengerFactory.create_batch(size=2)
        self.order = OrderFactory(passengers=(self.p1, self.p2))
        self.order_item = OrderItemFactory(order=self.order, trip=self.trip)

    def test_string_representation(self):
        self.assertEqual(str(self.p1), f"{self.p1.first_name}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.p1._meta.verbose_name_plural), "passengers")

    def test_passenger_model_creation_is_correct(self):
        Passenger.objects.all().delete()

        self.assertEqual(Passenger.objects.count(), 0)

        p1 = PassengerFactory()
        p1_from_db = Passenger.objects.first()

        self.assertEqual(Passenger.objects.count(), 1)

        self.assertEqual(p1.document_type, p1_from_db.document_type)
        self.assertEqual(p1.document_number, p1_from_db.document_number)
        self.assertEqual(p1.nationality, p1_from_db.nationality)
        self.assertEqual(p1.first_name, p1_from_db.first_name)
        self.assertEqual(p1.last_name, p1_from_db.last_name)
        self.assertEqual(p1.gender, p1_from_db.gender)
        self.assertEqual(p1.birth_date, p1_from_db.birth_date)
        self.assertEqual(p1.phone_number, p1_from_db.phone_number)

        _ = PassengerFactory()

        self.assertEqual(Passenger.objects.count(), 2)

    def test_first_and_last_name_max_length(self):
        p1 = Passenger.objects.first()

        first_name_max_length = p1._meta.get_field(  # type:ignore
            "first_name"
        ).max_length

        last_name_max_length = p1._meta.get_field("last_name").max_length  # type:ignore

        self.assertEqual(first_name_max_length, 50)
        self.assertEqual(last_name_max_length, 50)

    def test_passengers_are_ordered_by_created_date(self):
        ordering = self.p1._meta.ordering[0]  # type:ignore

        self.assertEqual(ordering, "-created_on")
