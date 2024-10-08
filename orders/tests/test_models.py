from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse_lazy

from faker import Faker

from base.models import Settings
from coupons.factories import CouponFactory
from orders.factories import (
    OrderFactory,
    OrderItemFactory,
    OrderWithCouponFactory,
    PassengerFactory,
)
from orders.models import Order, OrderItem, Passenger
from trips.factories import SeatFactory, TripFactory, TripTomorrowFactory
from trips.models import Seat, Trip

fake = Faker()


class OrderModelTests(TestCase):
    """Test suite for the Order Model"""

    def setUp(self) -> None:
        self.passengers = PassengerFactory.create_batch(size=2)
        self.order = OrderFactory(passengers=self.passengers)

    def test_str_representation(self):
        self.assertEqual(str(self.order), f"{self.order.name}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.order._meta.verbose_name), "order")
        self.assertEqual(str(self.order._meta.verbose_name_plural), "orders")

    def test_order_model_creation_is_accurate(self):
        order_from_db = Order.objects.first()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order_from_db.name, self.order.name)
        self.assertEqual(order_from_db.email, self.order.email)
        self.assertEqual(order_from_db.residence, self.order.residence)
        self.assertEqual(order_from_db.paid, self.order.paid)
        self.assertEqual(order_from_db.passengers.count(), len(self.passengers))

    def test_order_with_coupon_model_creation_is_accurate(self):
        Order.objects.all().delete()
        Passenger.objects.all().delete()

        order = OrderWithCouponFactory()
        order_from_db = Order.objects.first()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order_from_db.coupon, order.coupon)
        self.assertEqual(order_from_db.discount, order.discount)

    def test_order_with_coupon_model_creation_with_explicit_coupon(self):
        Order.objects.all().delete()
        Passenger.objects.all().delete()

        coupon = CouponFactory()
        _ = OrderFactory(coupon=coupon, discount=coupon.discount)
        order_from_db = Order.objects.first()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order_from_db.coupon, coupon)
        self.assertEqual(order_from_db.discount, coupon.discount)

    def test_order_name_max_length(self):
        order = Order.objects.first()
        max_length = order._meta.get_field("name").max_length

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
        ordering = order._meta.ordering[0]

        self.assertEqual(ordering, "-created_on")

    def test_order_total_cost_is_correct(self):
        order = Order.objects.first()

        order_item_1 = OrderItemFactory(order=order)
        order_item_2 = OrderItemFactory(order=order)

        expected = order_item_1.get_cost() + order_item_2.get_cost()
        actual = order.get_total_cost()

        self.assertEqual(actual, expected)

    def test_confirming_an_order_works(self):
        """
        This is a massive test veer where we check the complete order confirmation process.
        We take the following approach

        Arrange: We build the Order - Passengers | Trip - Seats | Order Items models
        Act: We put the seats on hold and then finally confirm the order
        Assert: Finally we verify that seats have correct status (Hold|Booked) and if booked
        there is a passenger assigned to it.

        """
        # Arrange
        # Clear the db
        Trip.objects.all().delete()
        Order.objects.all().delete()
        Passenger.objects.all().delete()

        # Create two trips with two available seats each
        trip = TripTomorrowFactory()
        SeatFactory.reset_sequence(1)
        seat_1, seat_2 = SeatFactory.create_batch(
            size=2, trip=trip, seat_status=Seat.AVAILABLE
        )

        # Create an unpaid order with two passengers
        passengers = PassengerFactory.create_batch(size=2)
        order = OrderFactory(passengers=passengers, paid=False)
        OrderItemFactory(order=order, trip=trip, quantity=2, seats="1, 2")

        self.assertFalse(order.paid)
        self.assertEqual(order.payment_id, "")
        self.assertTrue(seat_1.seat_status, Seat.AVAILABLE)
        self.assertTrue(seat_2.seat_status, Seat.AVAILABLE)

        self.assertIsNone(seat_1.passenger)
        self.assertIsNone(seat_2.passenger)

        # Act: now we confirm the order
        payment_id = fake.bban()
        order.confirm(payment_id=payment_id)

        # Assert: order
        order.refresh_from_db()
        trip.refresh_from_db()
        seat_1.refresh_from_db()
        seat_2.refresh_from_db()

        self.assertTrue(order.paid)
        self.assertEqual(order.payment_id, payment_id)

        self.assertTrue(seat_1.seat_status, Seat.BOOKED)
        self.assertTrue(seat_2.seat_status, Seat.BOOKED)

        self.assertIsNotNone(seat_1.passenger)
        self.assertIsNotNone(seat_2.passenger)

        self.assertIn(seat_1.passenger, passengers)
        self.assertIn(seat_2.passenger, passengers)

    def test_order_ticket_pdf_url_works(self):
        order = Order.objects.first()

        expected = reverse_lazy("orders:ticket_pdf", args=[str(order.id)])
        actual = order.get_ticket_url()

        self.assertEqual(actual, expected)

    def test_order_with_no_coupon_has_zero_discount(self):
        self.assertEqual(self.order.get_discount(), Decimal(0))

    def test_order_with_coupon_has_the_coupon_discount(self):
        discount = 10

        coupon = CouponFactory(discount=discount)
        order = OrderFactory(coupon=coupon, discount=discount)

        self.assertEqual(order.discount, coupon.discount)

    def test_order_get_discount_is_correctly_calculated(self):
        discount = 10

        coupon = CouponFactory(discount=discount)
        order = OrderFactory(coupon=coupon, discount=discount)
        outbound_trip = TripFactory()
        return_trip = TripTomorrowFactory()
        _ = [
            OrderItemFactory(order=order, trip=outbound_trip),
            OrderItemFactory(order=order, trip=return_trip),
        ]
        expected = order.get_total_cost_before_discount() * (
            order.discount / Decimal(100)
        )
        actual = order.get_discount()

        self.assertEqual(expected, actual)

    def test_order_total_cost_is_correct_when_discount_is_applied(self):
        discount = 10
        coupon = CouponFactory(discount=discount)
        order = OrderFactory(coupon=coupon, discount=discount)

        outbound_trip = TripFactory()
        return_trip = TripTomorrowFactory()
        _ = [
            OrderItemFactory(order=order, trip=outbound_trip),
            OrderItemFactory(order=order, trip=return_trip),
        ]

        expected = order.get_total_cost_before_discount() - order.get_discount()
        actual = order.get_total_cost()

        self.assertEqual(expected, actual)

    def test_order_total_cost_is_correct_when_discount_value_is_zero(self):
        # Create a coupon with zero discount
        discount = 0
        coupon = CouponFactory(discount=discount)
        order = OrderFactory(coupon=coupon, discount=discount)

        outbound_trip = TripFactory()
        return_trip = TripTomorrowFactory()
        _ = [
            OrderItemFactory(order=order, trip=outbound_trip),
            OrderItemFactory(order=order, trip=return_trip),
        ]
        expected = order.get_total_cost_before_discount() - order.get_discount()
        actual = order.get_total_cost()

        self.assertEqual(expected, actual)
        self.assertEqual(order.get_discount(), Decimal(0))

    def test_order_cost_in_usd(self):
        # Arrange: let's create an order in ARS

        PRICE_ARS = 70000  # cost of ticket
        USD_ARS = 950  # i.e 1 usd = 950 ars
        QTY = 2  # num of passengers

        order = OrderFactory(paid=False)
        OrderItemFactory(order=order, price=PRICE_ARS, quantity=QTY)

        Settings.objects.create(name="usd-ars", dec_val=USD_ARS)

        self.assertEqual(order.get_total_cost(), PRICE_ARS * QTY)

        # Act
        cost_usd = (PRICE_ARS * QTY) / USD_ARS
        cost_usd = Decimal(cost_usd)
        expected = round(cost_usd, 2)
        actual = order.get_total_cost_usd()

        # Assert
        self.assertEqual(actual, expected)


class OrderItemModelTests(TestCase):
    """Test suite for the OrderItem Model"""

    def setUp(self):
        self.trip = TripFactory()
        self.passengers = PassengerFactory.create_batch(size=2)
        self.order = OrderFactory(passengers=self.passengers)
        self.order_item = OrderItemFactory(order=self.order, trip=self.trip)

    def test_string_representation(self):
        self.assertEqual(str(self.order_item), f"OrderItem {self.order_item.id}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.order_item._meta.verbose_name_plural), "order items")

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

    def test_order_item_check_in_url(self):
        actual = self.order_item.get_checkin_url()
        base_url = f"/companies/{self.order_item.trip.company.slug}/admin/"
        checkin_url = f"orders/{self.order.id}/{self.order_item.id}/checkin/"
        expected = base_url + checkin_url

        self.assertEqual(actual, expected)


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
        self.assertEqual(str(self.p1._meta.verbose_name), "passenger")
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

        first_name_max_length = p1._meta.get_field("first_name").max_length

        last_name_max_length = p1._meta.get_field("last_name").max_length

        self.assertEqual(first_name_max_length, 50)
        self.assertEqual(last_name_max_length, 50)

    def test_passengers_are_ordered_by_created_date(self):
        ordering = self.p1._meta.ordering[0]

        self.assertEqual(ordering, "-created_on")

    def test_passenger_document_number_is_unique(self):
        # Arrange
        Passenger.objects.all().delete()

        # Act
        DOC_NUM = "A1234567"
        _ = PassengerFactory(document_number=DOC_NUM)

        self.assertEqual(Passenger.objects.count(), 1)
        self.assertEqual(Passenger.objects.first().document_number, DOC_NUM)

        # Assert
        with self.assertRaises(IntegrityError):
            _ = PassengerFactory(document_number=DOC_NUM)
