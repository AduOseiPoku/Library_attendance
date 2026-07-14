from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import AttendanceLog, LibrarySystemState


class AttendanceModelTests(TestCase):
    """Test the AttendanceLog model."""

    def test_create_attendance_log(self):
        """A log can be created with identifier, name, and default Active status."""
        log = AttendanceLog.objects.create(identifier='10010000', student_name='John Doe')
        self.assertEqual(log.identifier, '10010000')
        self.assertEqual(log.student_name, 'John Doe')
        self.assertEqual(log.status, 'Active')
        self.assertIsNotNone(log.timestamp_in)
        self.assertIsNone(log.timestamp_out)

    def test_str_representation(self):
        """The string representation shows identifier and status."""
        log = AttendanceLog.objects.create(identifier='10010000', student_name='John Doe')
        self.assertEqual(str(log), '10010000 - Active')


class HomePageTests(TestCase):
    """Test the homepage / landing screen."""

    def setUp(self):
        self.client = Client()

    def test_homepage_loads(self):
        """The homepage should load with a 200 status and show choice buttons."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'School Library')
        self.assertContains(response, 'Check In')
        self.assertContains(response, 'Check Out')


class CheckInTests(TestCase):
    """Test the check-in flow."""

    def setUp(self):
        self.client = Client()
        state = LibrarySystemState.get_state()
        state.is_open = True
        state.save()

    def test_successful_checkin(self):
        """A student can check in with ID and name."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': 'John Doe',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, John Doe!')
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 1)

    def test_checkin_creates_correct_record(self):
        """Check-in creates a log with the correct data."""
        self.client.post(reverse('checkin'), {
            'student_id': '20010000',
            'student_name': 'Jane Smith',
        })
        log = AttendanceLog.objects.get(identifier='20010000')
        self.assertEqual(log.student_name, 'Jane Smith')
        self.assertEqual(log.status, 'Active')
        self.assertIsNone(log.timestamp_out)


    def test_checkin_short_id(self):
        """Check-in should fail if student ID is less than 8 digits."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '1234567',
            'student_name': 'John Doe',
        })
        self.assertContains(response, 'exactly 8 digits')
        self.assertEqual(AttendanceLog.objects.count(), 0)

    def test_checkin_long_id(self):
        """Check-in should fail if student ID is more than 8 digits."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '123456789',
            'student_name': 'John Doe',
        })
        self.assertContains(response, 'exactly 8 digits')
        self.assertEqual(AttendanceLog.objects.count(), 0)

    def test_checkin_non_digit_id(self):
        """Check-in should fail if student ID contains non-digits."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '1234abcd',
            'student_name': 'John Doe',
        })
        self.assertContains(response, 'exactly 8 digits')
        self.assertEqual(AttendanceLog.objects.count(), 0)

    def test_checkin_missing_id(self):
        """Check-in should fail if student ID is missing."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '',
            'student_name': 'John Doe',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter both')
        self.assertEqual(AttendanceLog.objects.count(), 0)

    def test_checkin_missing_name(self):
        """Check-in should fail if student name is missing."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter both')
        self.assertEqual(AttendanceLog.objects.count(), 0)

    def test_checkin_missing_both(self):
        """Check-in should fail if both fields are missing."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '',
            'student_name': '',
        })
        self.assertContains(response, 'Please enter both')
        self.assertEqual(AttendanceLog.objects.count(), 0)

    def test_get_request_redirects(self):
        """A GET request to /checkin/ should redirect to home."""
        response = self.client.get(reverse('checkin'))
        self.assertEqual(response.status_code, 302)


class DuplicateCheckInTests(TestCase):
    """Test duplicate check-in prevention."""

    def setUp(self):
        self.client = Client()
        state = LibrarySystemState.get_state()
        state.is_open = True
        state.save()
        # Check in a student first
        AttendanceLog.objects.create(identifier='10010000', student_name='John Doe', status='Active')

    def test_exact_duplicate_blocked(self):
        """Same ID + same name should be blocked."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': 'John Doe',
        })
        self.assertContains(response, 'already checked in')
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 1)

    def test_case_insensitive_duplicate_blocked(self):
        """Same ID + same name (different case) should be blocked."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': 'john doe',
        })
        self.assertContains(response, 'already checked in')
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 1)

    def test_same_id_different_name_shows_conflict(self):
        """Same ID but different name should show the conflict screen."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': 'Jane Smith',
        })
        self.assertContains(response, 'Hold on!')
        self.assertContains(response, 'John Doe')
        # No new record should be created yet
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 1)

    def test_same_name_different_id_shows_conflict(self):
        """Same name but different ID should show the conflict screen."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '99990000',
            'student_name': 'John Doe',
        })
        self.assertContains(response, 'Hold on!')
        # No new record should be created yet
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 1)

    def test_force_checkin_after_id_conflict(self):
        """Forcing check-in after ID conflict should create a new record."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': 'Jane Smith',
            'force_checkin': 'yes',
        })
        self.assertContains(response, 'Welcome, Jane Smith!')
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 2)

    def test_force_checkin_after_name_conflict(self):
        """Forcing check-in after name conflict should create a new record."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '99990000',
            'student_name': 'John Doe',
            'force_checkin': 'yes',
        })
        self.assertContains(response, 'Welcome, John Doe!')
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 2)

    def test_completed_student_can_checkin_again(self):
        """A student who has completed checkout can check in again."""
        log = AttendanceLog.objects.get(identifier='10010000')
        log.status = 'Completed'
        log.timestamp_out = timezone.now()
        log.save()

        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': 'John Doe',
        })
        self.assertContains(response, 'Welcome, John Doe!')
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 1)


class QuickCheckoutTests(TestCase):
    """Test the tap-to-checkout flow."""

    def setUp(self):
        self.client = Client()
        state = LibrarySystemState.get_state()
        state.is_open = True
        state.save()
        self.log = AttendanceLog.objects.create(identifier='10010000', student_name='John Doe', status='Active')

    def test_successful_checkout(self):
        """Tapping a name should check them out."""
        response = self.client.post(reverse('quick_checkout'), {
            'log_id': self.log.id,
        })
        self.assertContains(response, 'Goodbye, John Doe!')
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'Completed')
        self.assertIsNotNone(self.log.timestamp_out)

    def test_checkout_invalid_id(self):
        """Checking out with an invalid log ID should show an error."""
        response = self.client.post(reverse('quick_checkout'), {
            'log_id': 99999,
        })
        self.assertContains(response, 'Could not find')

    def test_checkout_already_completed(self):
        """Checking out a log that is already Completed should show an error."""
        self.log.status = 'Completed'
        self.log.timestamp_out = timezone.now()
        self.log.save()

        response = self.client.post(reverse('quick_checkout'), {
            'log_id': self.log.id,
        })
        self.assertContains(response, 'Could not find')

    def test_get_request_redirects(self):
        """A GET request to /checkout/ should redirect to home."""
        response = self.client.get(reverse('quick_checkout'))
        self.assertEqual(response.status_code, 302)


class DashboardLoginTests(TestCase):
    """Test the librarian dashboard login."""

    def setUp(self):
        self.client = Client()

    def test_login_page_loads(self):
        """The login page should render properly."""
        response = self.client.get(reverse('dashboard_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Librarian Login')

    def test_correct_password(self):
        """Correct password should redirect to dashboard."""
        response = self.client.post(reverse('dashboard_login'), {
            'password': 'admin123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_wrong_password(self):
        """Wrong password should stay on login page with error."""
        response = self.client.post(reverse('dashboard_login'), {
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Incorrect password')

    def test_empty_password(self):
        """Empty password should stay on login page."""
        response = self.client.post(reverse('dashboard_login'), {
            'password': '',
        })
        self.assertEqual(response.status_code, 200)


class DashboardTests(TestCase):
    """Test the librarian dashboard."""

    def setUp(self):
        self.client = Client()
        # Log in first
        self.client.post(reverse('dashboard_login'), {'password': 'admin123'})
        # Create some test data
        self.active_log = AttendanceLog.objects.create(
            identifier='10010000', student_name='John Doe', status='Active'
        )
        self.completed_log = AttendanceLog.objects.create(
            identifier='10020000', student_name='Jane Smith', status='Completed',
            timestamp_out=timezone.now()
        )

    def test_dashboard_loads_when_logged_in(self):
        """Dashboard should load with correct data when authenticated."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Librarian Dashboard')
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Jane Smith')

    def test_dashboard_redirects_when_not_logged_in(self):
        """Dashboard should redirect unauthenticated users to login."""
        client = Client()  # fresh client, no session
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_shows_metrics(self):
        """Dashboard should display the correct metrics."""
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Currently Inside:')
        self.assertContains(response, 'Total Today:')

    def test_manual_checkout_from_dashboard(self):
        """Librarian can manually check out a student from the dashboard."""
        response = self.client.post(reverse('dashboard'), {
            'log_id': self.active_log.id,
        })
        self.assertEqual(response.status_code, 302)
        self.active_log.refresh_from_db()
        self.assertEqual(self.active_log.status, 'Completed')
        self.assertIsNotNone(self.active_log.timestamp_out)

    def test_manual_checkout_invalid_id(self):
        """Manual checkout with invalid ID should not crash."""
        response = self.client.post(reverse('dashboard'), {
            'log_id': 99999,
        })
        self.assertEqual(response.status_code, 302)


class MultipleStudentFlowTests(TestCase):
    """Test realistic multi-student scenarios."""

    def setUp(self):
        self.client = Client()
        state = LibrarySystemState.get_state()
        state.is_open = True
        state.save()

    def test_multiple_students_checkin(self):
        """Multiple different students can check in simultaneously."""
        self.client.post(reverse('checkin'), {'student_id': '10010000', 'student_name': 'John Doe'})
        self.client.post(reverse('checkin'), {'student_id': '10020000', 'student_name': 'Jane Smith'})
        self.client.post(reverse('checkin'), {'student_id': '10030000', 'student_name': 'Alex Kwame'})
        self.assertEqual(AttendanceLog.objects.filter(status='Active').count(), 3)

    def test_checkin_checkout_checkin_cycle(self):
        """A student can check in, check out, and check in again."""
        # Check in
        self.client.post(reverse('checkin'), {'student_id': '10010000', 'student_name': 'John Doe'})
        log = AttendanceLog.objects.get(identifier='10010000', status='Active')

        # Check out
        self.client.post(reverse('quick_checkout'), {'log_id': log.id})
        log.refresh_from_db()
        self.assertEqual(log.status, 'Completed')

        # Check in again
        response = self.client.post(reverse('checkin'), {'student_id': '10010000', 'student_name': 'John Doe'})
        self.assertContains(response, 'Welcome, John Doe!')
        self.assertEqual(AttendanceLog.objects.filter(identifier='10010000', status='Active').count(), 1)
        self.assertEqual(AttendanceLog.objects.filter(identifier='10010000').count(), 2)

    def test_checkout_list_shows_on_homepage(self):
        """The checkout list on the homepage should show active students."""
        AttendanceLog.objects.create(identifier='10010000', student_name='John Doe', status='Active')
        AttendanceLog.objects.create(identifier='10020000', student_name='Jane Smith', status='Active')

        response = self.client.get(reverse('home'))
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Jane Smith')

    def test_completed_students_not_in_checkout_list(self):
        """Completed students should not appear in the checkout list."""
        AttendanceLog.objects.create(identifier='10010000', student_name='John Doe', status='Active')
        AttendanceLog.objects.create(
            identifier='10020000', student_name='Jane Smith', status='Completed',
            timestamp_out=timezone.now()
        )

        response = self.client.get(reverse('home'))
        self.assertContains(response, 'John Doe')
        active_logs = response.context['active_logs']
        self.assertEqual(active_logs.count(), 1)


class LibraryClosedTests(TestCase):
    """Test that check-in is blocked when library is closed."""

    def setUp(self):
        self.client = Client()
        # Library defaults to closed, so don't open it

    def test_checkin_blocked_when_closed(self):
        """Check-in should redirect with error when library is closed."""
        response = self.client.post(reverse('checkin'), {
            'student_id': '10010000',
            'student_name': 'John Doe',
        }, follow=True)
        self.assertContains(response, 'Library is Currently Closed', status_code=200)
        self.assertEqual(AttendanceLog.objects.count(), 0)
