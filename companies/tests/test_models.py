from django.db import IntegrityError
from django.test import TestCase

from companies.factories import CompanyFactory
from companies.models import Company, company_cover_path, company_thumbnail_path
from users.factories import CompanyOwnerFactory


class CompanyModelTests(TestCase):
    """Test suite for the Company Model"""

    def setUp(self):
        self.company = CompanyFactory()

    def test_string_representation(self):
        self.assertEqual(str(self.company), self.company.name)

    def test_get_absolute_url(self):
        expected_url = f"/companies/{self.company.slug.lower()}/"
        self.assertEqual(self.company.get_absolute_url(), expected_url)

    def test_get_admin_url(self):
        expected_url = f"/companies/{self.company.slug.lower()}/admin/"

        self.assertEqual(self.company.get_admin_url(), expected_url)

    def test_get_trip_list_url(self):
        expected_url = f"/companies/{self.company.slug.lower()}/admin/trips/"

        self.assertEqual(self.company.get_trip_list_url(), expected_url)

    def test_get_coupon_list_url(self):
        expected_url = f"/companies/{self.company.slug.lower()}/admin/coupons/"

        self.assertEqual(self.company.get_coupon_list_url(), expected_url)

    def test_get_booking_url(self):
        expected_url = f"/companies/{self.company.slug.lower()}/book/"

        self.assertEqual(self.company.get_booking_url(), expected_url)

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.company._meta.verbose_name_plural), "companies")

    def test_company_model_creation_is_accurate(self):
        company_from_db = Company.objects.first()

        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(company_from_db.name, self.company.name)
        self.assertEqual(company_from_db.slug, self.company.slug)
        self.assertEqual(company_from_db.owner, self.company.owner)

    def test_company_name_max_length(self):
        company = Company.objects.first()
        max_length = company._meta.get_field("name").max_length

        self.assertEqual(max_length, 200)

    def test_company_slug_max_length(self):
        company = Company.objects.first()
        max_length = company._meta.get_field("slug").max_length

        self.assertEqual(max_length, 300)

    def test_all_companies_have_unique_slugs(self):
        Company.objects.all().delete()
        Company.objects.create(name="Andesmar", slug="andesmar")

        with self.assertRaises(IntegrityError):
            Company.objects.create(name="Andes a Mar", slug="andesmar")

    def test_all_companies_are_ordered_correctly(self):
        Company.objects.all().delete()

        c_1 = Company.objects.create(name="cata", slug="cata")
        c_2 = Company.objects.create(name="Bariloche Travels", slug="bari-travels")
        c_3 = Company.objects.create(name="Andesmar", slug="andesmar")

        companies = Company.objects.all()

        self.assertEqual(companies[0], c_3)
        self.assertEqual(companies[1], c_2)
        self.assertEqual(companies[2], c_1)

        company = companies[0]
        ordering = company._meta.ordering[0]

        self.assertEqual(ordering, "name")

    def test_company_slug_is_auto_generated_even_if_not_supplied(self):
        owner = CompanyOwnerFactory()

        # create company but do not pass slug
        company = Company.objects.create(
            name="20 de junio",
            address="Mendoza Argentina",
            phone="5491150254191",
            email="comercial@20dejunio.com",
            owner=owner,
        )

        expected = "20-de-junio"
        actual = company.slug

        self.assertEqual(expected, actual)

        # Update the company name. This should not update the slug itself
        # else it breaks our SEO
        new_name = "20 DE JUNIO"
        obj, created = Company.objects.update_or_create(
            name="20 de junio", defaults={"name": new_name}
        )

        self.assertEqual(obj.slug, expected)
        self.assertEqual(obj.name, new_name)


class CompanyImagePaths(TestCase):
    def setUp(self) -> None:
        self.company = CompanyFactory()

    def test_company_cover_path_is_correct(self):
        filename = "cover.jpg"
        actual = company_cover_path(instance=self.company, filename=filename)
        expected = f"companies/{self.company.slug}/covers/{filename}"

        self.assertEqual(actual, expected)

    def test_company_thumbnail_path_is_correct(self):
        filename = "thumbnail.jpg"
        actual = company_thumbnail_path(instance=self.company, filename=filename)
        expected = f"companies/{self.company.slug}/thumbnails/{filename}"

        self.assertEqual(actual, expected)
