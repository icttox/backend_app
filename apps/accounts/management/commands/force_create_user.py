from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a user directly bypassing admin interface'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument('password', type=str, help='User password')
        parser.add_argument('--first_name', type=str, help='First name', default='')
        parser.add_argument('--last_name', type=str, help='Last name', default='')
        parser.add_argument('--is_staff', action='store_true', help='Is staff user')
        parser.add_argument('--is_superuser', action='store_true', help='Is superuser')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        is_staff = options.get('is_staff', False)
        is_superuser = options.get('is_superuser', False)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'User with email {email} already exists'))
            return
            
        # Create the user using the model manager to ensure proper username generation
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        
        # Print the generated username
        self.stdout.write(self.style.SUCCESS(f'User created successfully with username: {user.username}'))
        self.stdout.write(self.style.SUCCESS(f'User ID: {user.id}'))
        
        # Verify the profile was created by the signal
        if hasattr(user, 'profile'):
            self.stdout.write(self.style.SUCCESS(f'User profile created with ID: {user.profile.id}'))
        else:
            self.stdout.write(self.style.WARNING('User profile was not automatically created'))
