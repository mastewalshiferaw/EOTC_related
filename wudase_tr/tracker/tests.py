import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import DailyReview, Paragraph, ReviewLog

MEDIA_ROOT = tempfile.mkdtemp(prefix="wudase-test-media-")
GE = "\u1230"  # ETHIOPIC SYLLABLE SA


def make_image(name="page.png"):
    buf = io.BytesIO()
    Image.new("RGB", (12, 12), "white").save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


def backdate_daily_review(user, days_ago):
    return DailyReview.objects.create(
        user=user, date=timezone.localdate() - timedelta(days=days_ago)
    )


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    # Real PBKDF2 hashing costs seconds per fixture; not what these tests check.
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class TrackerTestCase(TestCase):
    """Shared fixtures: two users, each able to own paragraphs."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pw-alice-123")
        self.other = User.objects.create_user("bob", password="pw-bob-123")
        self.client.login(username="alice", password="pw-alice-123")

    def make_paragraph(self, user=None, day="Monday", order=1):
        return Paragraph.objects.create(
            user=user or self.user,
            image=make_image(),
            day_name=day,
            order_index=order,
        )


class AuthenticationTests(TrackerTestCase):
    """Every tracker view must be closed to anonymous visitors."""

    def setUp(self):
        super().setUp()
        self.para = self.make_paragraph()
        self.client.logout()

    def test_protected_pages_redirect_to_login(self):
        # Trailing-slash normalisation can rewrite the next= value, so compare paths.
        urls = [
            reverse("dashboard"),
            reverse("upload_view"),
            reverse("daily_recall"),
            reverse("edit_paragraph", args=[self.para.pk]),
            reverse("delete_paragraph", args=[self.para.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response["Location"])
                self.assertIn(url.rstrip("/"), response["Location"])

    def test_anonymous_post_cannot_mutate_data(self):
        response = self.client.post(
            reverse("daily_recall"), {"para_id": self.para.pk, "rating": "3"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReviewLog.objects.count(), 0)
        self.para.refresh_from_db()
        self.assertIsNone(self.para.last_reviewed)

    def test_anonymous_delete_post_is_blocked(self):
        response = self.client.post(reverse("delete_paragraph", args=[self.para.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Paragraph.objects.filter(pk=self.para.pk).exists())

    def test_login_page_renders(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)

class DashboardTests(TrackerTestCase):
    def test_empty_library(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["paragraphs"]), [])
        self.assertEqual(response.context["streak"], 0)
        self.assertContains(response, "No paragraphs yet")
        self.assertContains(response, "Current Streak: 0 Days")

    def test_lists_only_own_paragraphs(self):
        mine = self.make_paragraph(day="Monday")
        self.make_paragraph(user=self.other, day="Tuesday")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(list(response.context["paragraphs"]), [mine])

    def test_streak_zero_without_reviews(self):
        self.make_paragraph()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["streak"], 0)

    def test_streak_counts_today(self):
        backdate_daily_review(self.user, 0)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["streak"], 1)

    def test_streak_grace_period_when_today_not_done_yet(self):
        """Yesterday and the day before count even if today is not reviewed yet."""
        backdate_daily_review(self.user, 1)
        backdate_daily_review(self.user, 2)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["streak"], 2)

    def test_streak_stops_at_gap(self):
        for days in (0, 1, 2, 4, 5):
            backdate_daily_review(self.user, days)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["streak"], 3)

    def test_streak_ignores_other_users(self):
        backdate_daily_review(self.other, 0)
        backdate_daily_review(self.other, 1)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["streak"], 0)

    def test_streak_banner_renders_once(self):
        """Regression: the banner used to be inside the paragraph loop."""
        for order in (1, 2, 3):
            self.make_paragraph(order=order)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.content.decode().count("Current Streak"), 1)

    def test_average_rating_annotation(self):
        para = self.make_paragraph()
        ReviewLog.objects.create(user=self.user, paragraph=para, rating=1)
        ReviewLog.objects.create(user=self.user, paragraph=para, rating=3)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["paragraphs"][0].avg_rating, 2.0)

    def test_average_rating_is_none_without_reviews(self):
        self.make_paragraph()
        response = self.client.get(reverse("dashboard"))
        self.assertIsNone(response.context["paragraphs"][0].avg_rating)


class UploadTests(TrackerTestCase):
    def test_get_renders_form(self):
        response = self.client.get(reverse("upload_view"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_valid_upload_assigns_current_user(self):
        response = self.client.post(
            reverse("upload_view"),
            {"day_name": "Monday", "order_index": "1", "image": make_image()},
        )
        self.assertRedirects(response, reverse("dashboard"))
        para = Paragraph.objects.get()
        self.assertEqual(para.user, self.user)
        self.assertEqual(para.day_name, "Monday")
        self.assertEqual(para.order_index, 1)

    def test_upload_without_image_is_rejected(self):
        response = self.client.post(
            reverse("upload_view"), {"day_name": "Monday", "order_index": "1"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.context["form"].errors)
        self.assertEqual(Paragraph.objects.count(), 0)

    def test_upload_without_day_name_is_rejected(self):
        response = self.client.post(
            reverse("upload_view"), {"order_index": "1", "image": make_image()}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("day_name", response.context["form"].errors)
        self.assertEqual(Paragraph.objects.count(), 0)

    def test_upload_with_non_integer_order_is_rejected(self):
        response = self.client.post(
            reverse("upload_view"),
            {"day_name": "Monday", "order_index": "first", "image": make_image()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("order_index", response.context["form"].errors)
        self.assertEqual(Paragraph.objects.count(), 0)

    def test_upload_rejects_non_image_payload(self):
        bogus = SimpleUploadedFile("notes.txt", b"not an image", content_type="text/plain")
        response = self.client.post(
            reverse("upload_view"),
            {"day_name": "Monday", "order_index": "1", "image": bogus},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.context["form"].errors)
        self.assertEqual(Paragraph.objects.count(), 0)

    def test_upload_cannot_set_owner_via_post(self):
        response = self.client.post(
            reverse("upload_view"),
            {
                "day_name": "Monday",
                "order_index": "1",
                "image": make_image(),
                "user": self.other.pk,
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(Paragraph.objects.get().user, self.user)

    def test_unicode_day_name_round_trip(self):
        response = self.client.post(
            reverse("upload_view"),
            {"day_name": GE + "lo", "order_index": "2", "image": make_image()},
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(Paragraph.objects.get().day_name, GE + "lo")

class EditTests(TrackerTestCase):
    def test_edit_form_prefilled(self):
        para = self.make_paragraph(day="Friday", order=4)
        response = self.client.get(reverse("edit_paragraph", args=[para.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Friday")
        self.assertEqual(response.context["form"].instance, para)

    def test_edit_updates_fields(self):
        para = self.make_paragraph(day="Friday", order=4)
        response = self.client.post(
            reverse("edit_paragraph", args=[para.pk]),
            {"day_name": "Sunday", "order_index": "9"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        para.refresh_from_db()
        self.assertEqual(para.day_name, "Sunday")
        self.assertEqual(para.order_index, 9)

    def test_cannot_edit_another_users_paragraph(self):
        theirs = self.make_paragraph(user=self.other)
        response = self.client.get(reverse("edit_paragraph", args=[theirs.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_post_to_another_users_paragraph(self):
        theirs = self.make_paragraph(user=self.other, day="Friday")
        response = self.client.post(
            reverse("edit_paragraph", args=[theirs.pk]),
            {"day_name": "Sunday", "order_index": "9"},
        )
        self.assertEqual(response.status_code, 404)
        theirs.refresh_from_db()
        self.assertEqual(theirs.day_name, "Friday")

    def test_edit_missing_paragraph_is_404(self):
        response = self.client.get(reverse("edit_paragraph", args=[99999]))
        self.assertEqual(response.status_code, 404)


class DeleteTests(TrackerTestCase):
    def test_confirm_page_renders(self):
        """Regression: the template used to sit outside the templates directory."""
        para = self.make_paragraph()
        response = self.client.get(reverse("delete_paragraph", args=[para.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["para"], para)

    def test_get_does_not_delete(self):
        para = self.make_paragraph()
        self.client.get(reverse("delete_paragraph", args=[para.pk]))
        self.assertTrue(Paragraph.objects.filter(pk=para.pk).exists())

    def test_post_deletes(self):
        para = self.make_paragraph()
        response = self.client.post(reverse("delete_paragraph", args=[para.pk]))
        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(Paragraph.objects.filter(pk=para.pk).exists())

    def test_cannot_delete_another_users_paragraph(self):
        theirs = self.make_paragraph(user=self.other)
        response = self.client.post(reverse("delete_paragraph", args=[theirs.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Paragraph.objects.filter(pk=theirs.pk).exists())

    def test_delete_missing_paragraph_is_404(self):
        response = self.client.post(reverse("delete_paragraph", args=[99999]))
        self.assertEqual(response.status_code, 404)


class RecallLoopTests(TrackerTestCase):
    def test_empty_library_shows_finished(self):
        response = self.client.get(reverse("daily_recall"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/finished.html")

    def test_everything_reviewed_today_shows_finished(self):
        para = self.make_paragraph()
        para.last_reviewed = timezone.localdate()
        para.save()
        response = self.client.get(reverse("daily_recall"))
        self.assertTemplateUsed(response, "tracker/finished.html")

    def test_shows_never_reviewed_paragraph_first(self):
        seen = self.make_paragraph(day="Monday", order=1)
        seen.last_reviewed = timezone.localdate() - timedelta(days=3)
        seen.save()
        fresh = self.make_paragraph(day="Tuesday", order=2)
        response = self.client.get(reverse("daily_recall"))
        self.assertEqual(response.context["para"], fresh)

    def test_does_not_serve_other_users_paragraphs(self):
        self.make_paragraph(user=self.other)
        response = self.client.get(reverse("daily_recall"))
        self.assertTemplateUsed(response, "tracker/finished.html")

    def test_progress_one_of_two_is_fifty_percent(self):
        done = self.make_paragraph(day="Monday", order=1)
        done.last_reviewed = timezone.localdate()
        done.save()
        self.make_paragraph(day="Tuesday", order=2)
        response = self.client.get(reverse("daily_recall"))
        self.assertEqual(response.context["remaining"], 1)
        self.assertEqual(response.context["total"], 2)
        self.assertEqual(response.context["percent_done"], 50)
        self.assertContains(response, "width: 50%")

    def test_progress_starts_at_zero(self):
        """Regression: the bar used to render the string 'True%'."""
        self.make_paragraph()
        response = self.client.get(reverse("daily_recall"))
        self.assertEqual(response.context["percent_done"], 0)
        self.assertContains(response, "width: 0%")
        self.assertNotContains(response, "True%")

    def test_counts_only_own_paragraphs_in_totals(self):
        self.make_paragraph(day="Monday", order=1)
        self.make_paragraph(user=self.other, day="Tuesday", order=1)
        self.make_paragraph(user=self.other, day="Wednesday", order=1)
        response = self.client.get(reverse("daily_recall"))
        self.assertEqual(response.context["total"], 1)
        self.assertEqual(response.context["remaining"], 1)

class RatingTests(TrackerTestCase):
    def test_each_valid_rating_is_persisted(self):
        para = self.make_paragraph()
        for rating in (1, 2, 3):
            with self.subTest(rating=rating):
                self.client.post(
                    reverse("daily_recall"),
                    {"para_id": para.pk, "rating": str(rating)},
                )
                self.assertEqual(
                    ReviewLog.objects.filter(paragraph=para).latest("id").rating, rating
                )

    def test_rating_marks_paragraph_reviewed_and_logs_daily(self):
        para = self.make_paragraph()
        response = self.client.post(
            reverse("daily_recall"), {"para_id": para.pk, "rating": "2"}
        )
        self.assertRedirects(response, reverse("daily_recall"))
        para.refresh_from_db()
        self.assertEqual(para.last_reviewed, timezone.localdate())
        log = DailyReview.objects.get(user=self.user)
        self.assertIn(para, log.paragraphs_reviewed.all())

    def test_missing_rating_defaults_to_forgot(self):
        para = self.make_paragraph()
        response = self.client.post(reverse("daily_recall"), {"para_id": para.pk})
        self.assertRedirects(response, reverse("daily_recall"))
        self.assertEqual(ReviewLog.objects.get().rating, ReviewLog.FORGOT)

    def test_non_numeric_rating_does_not_crash(self):
        """Regression: int('abc') used to raise ValueError and return 500."""
        para = self.make_paragraph()
        response = self.client.post(
            reverse("daily_recall"), {"para_id": para.pk, "rating": "abc"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReviewLog.objects.get().rating, ReviewLog.FORGOT)

    def test_out_of_range_rating_falls_back_to_forgot(self):
        para = self.make_paragraph()
        for bad in ("0", "99", "-1", "", " ", "2.5"):
            with self.subTest(rating=bad):
                ReviewLog.objects.all().delete()
                self.client.post(
                    reverse("daily_recall"), {"para_id": para.pk, "rating": bad}
                )
                self.assertEqual(ReviewLog.objects.get().rating, ReviewLog.FORGOT)

    def test_cannot_rate_another_users_paragraph(self):
        theirs = self.make_paragraph(user=self.other)
        response = self.client.post(
            reverse("daily_recall"), {"para_id": theirs.pk, "rating": "3"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ReviewLog.objects.count(), 0)
        theirs.refresh_from_db()
        self.assertIsNone(theirs.last_reviewed)

    def test_missing_paragraph_id_is_404(self):
        response = self.client.post(reverse("daily_recall"), {"rating": "1"})
        self.assertEqual(response.status_code, 404)

    def test_unknown_paragraph_id_is_404(self):
        response = self.client.post(
            reverse("daily_recall"), {"para_id": 99999, "rating": "1"}
        )
        self.assertEqual(response.status_code, 404)

    def test_repeated_reviews_share_one_daily_row(self):
        """Regression: get_or_create never matched, adding a row per review.

        DailyReview.date used auto_now_add, which stores the server's local date,
        while the view looked up timezone.localdate(). Whenever those differ every
        POST inserted a new row, so today's log grew without bound.
        """
        for _ in range(3):
            para = self.make_paragraph()
            response = self.client.post(
                reverse("daily_recall"), {"para_id": para.pk, "rating": "2"}
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(DailyReview.objects.filter(user=self.user).count(), 1)

    def test_daily_row_is_stamped_with_the_project_timezone_date(self):
        para = self.make_paragraph()
        self.client.post(reverse("daily_recall"), {"para_id": para.pk, "rating": "1"})
        self.assertEqual(DailyReview.objects.get(user=self.user).date, timezone.localdate())

    def test_review_log_date_matches_reviewed_paragraph_date(self):
        para = self.make_paragraph()
        self.client.post(reverse("daily_recall"), {"para_id": para.pk, "rating": "1"})
        para.refresh_from_db()
        self.assertEqual(ReviewLog.objects.get().reviewed_at, para.last_reviewed)

    def test_reviewing_all_paragraphs_reaches_finished(self):
        paras = [self.make_paragraph(order=i) for i in (1, 2)]
        for para in paras:
            self.client.post(
                reverse("daily_recall"), {"para_id": para.pk, "rating": "3"}
            )
        response = self.client.get(reverse("daily_recall"))
        self.assertTemplateUsed(response, "tracker/finished.html")
        log = DailyReview.objects.get(user=self.user)
        self.assertEqual(log.paragraphs_reviewed.count(), 2)


class ModelTests(TrackerTestCase):
    def test_paragraph_str(self):
        para = self.make_paragraph(day="Monday", order=1)
        self.assertEqual(str(para), "alice - Monday - Part 1")

    def test_review_log_str(self):
        para = self.make_paragraph(day="Monday", order=1)
        log = ReviewLog.objects.create(user=self.user, paragraph=para, rating=2)
        self.assertIn("alice reviewed Monday", str(log))

    def test_default_rating_is_forgot(self):
        para = self.make_paragraph()
        log = ReviewLog.objects.create(user=self.user, paragraph=para)
        self.assertEqual(log.rating, ReviewLog.FORGOT)

    def test_deleting_user_cascades_to_paragraphs(self):
        self.make_paragraph()
        self.user.delete()
        self.assertEqual(Paragraph.objects.count(), 0)

    def test_deleting_paragraph_keeps_daily_review_row(self):
        para = self.make_paragraph()
        log = DailyReview.objects.create(user=self.user)
        log.paragraphs_reviewed.add(para)
        para.delete()
        self.assertEqual(DailyReview.objects.count(), 1)
        self.assertEqual(DailyReview.objects.get().paragraphs_reviewed.count(), 0)
