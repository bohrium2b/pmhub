import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pmhub.settings'
from django import setup
setup()
from django.contrib.auth.models import Group, Permission, User
from signup.models import Concert, Performance

from django.core.management import execute_from_command_line

try:
    from rich import print
except Exception:
    pass


def creategroups() -> None:
    print("Creating group Event Managers ... ", end="")
    eventmanager = Group(name="event-manager")
    eventmanager.save()
    print("[green]Done![/green]")

def createusers() -> None:
    eventmanager: Group = Group.objects.get(name="event-manager")
    print("Creating superuser")
    firstname = input("First name: ")
    lastname = input("Last name: ")
    username = input("Username: ")
    password = input("Password: ")
    superuser = User.objects.create_superuser(username=username, password=password, first_name=firstname, last_name=lastname) # type: ignore
    superuser.groups.add(eventmanager)
    print("Creating demo users ... ", end="")
    users: list[dict[str, str | bool]] = [
        {"first": "Jungwon", "last": "Yang", "staff": True},
        {"first": "Heeseung", "last": "Lee", "staff": False},
        {"first": "Sunoo", "last": "Kim", "staff": False},
        {"first": "Jake", "last": "Sim", "staff": False},
        {"first": "Jay", "last": "Park", "staff": False},
        {"first": "Sunghoon", "last": "Park", "staff": False},
        {"first": "Nishimura", "last": "Riki", "staff": False},
        {"first": "Soobin", "last": "Choi", "staff": True},
        {"first": "Yeonjun", "last": "Choi", "staff": False},
        {"first": "Beomgyu", "last": "Choi", "staff": False},
        {"first": "Taehyun", "last": "Kang", "staff": False},
        {"first": "Kai-Kamal", "last": "Huening", "staff": False},
        {"first": "Junhui", "last": "Wen", "staff": False},
        {"first": "Minghao", "last": "Xu", "staff": False},
        {"first": "Christopher", "last": "Bang", "staff": True}
    ]
    for user in users:
        username: str = user["first"].lower() + user["last"].lower()
        newuser: User = User.objects.create_user(username, first_name=user["first"], last_name=user["last"], password=username)
        if user["staff"]:
            newuser.groups.add(eventmanager)
            newuser.is_staff = True
            newuser.save()
    print("Done!")


def main():
    print("[bold]Hello! This wizard will guide you through setting up your PMHub installation. [/bold]")
    print("[bold]We will now create the standard files like databases.[/bold]")
    execute_from_command_line(['manage.py', 'migrate'])
    print("Now, we will setup the groups for managers. ")
    creategroups()
    print("Now, we will create demo users.")
    createusers()
    print("All set! Run python manage.py runserver to try it out!")


if __name__ == "__main__":
    main()