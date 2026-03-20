import json
import os
import re
import sys
import logging

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_SUBS_FILE = os.path.join(_DATA_DIR, "subscribers.json")


def _ensure_file():
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_SUBS_FILE):
        with open(_SUBS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _is_valid_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def get_subscribers():
    _ensure_file()
    with open(_SUBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_subscribers(subs):
    _ensure_file()
    with open(_SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(set(subs)), f, indent=2)


def add_subscriber(email):
    email = email.strip().lower()
    if not _is_valid_email(email):
        return False, f"Invalid email format: {email}"

    subs = get_subscribers()
    if email in subs:
        return False, f"Already subscribed: {email}"

    subs.append(email)
    _save_subscribers(subs)
    logger.info(f"Added subscriber: {email}")
    return True, f"Added: {email}"


def remove_subscriber(email):
    email = email.strip().lower()
    subs = get_subscribers()
    if email not in subs:
        return False, f"Not found: {email}"

    subs.remove(email)
    _save_subscribers(subs)
    logger.info(f"Removed subscriber: {email}")
    return True, f"Removed: {email}"


def import_from_env():
    from dotenv import load_dotenv
    load_dotenv()
    env_subs = os.getenv("SUBSCRIBERS", "")
    added = 0
    for email in env_subs.split(","):
        email = email.strip()
        if email:
            ok, msg = add_subscriber(email)
            if ok:
                added += 1
            print(f"  {msg}")
    return added


def main():
    if len(sys.argv) < 2:
        print("SIFT Subscriber Manager")
        print("=" * 40)
        print()
        print("Commands:")
        print("  python subscribers.py list                     Show all subscribers")
        print("  python subscribers.py add <email> [email2...]  Add subscriber(s)")
        print("  python subscribers.py remove <email>           Remove a subscriber")
        print("  python subscribers.py import-env               Import from .env")
        print("  python subscribers.py count                    Show count")
        return

    cmd = sys.argv[1].lower()

    if cmd == "list":
        subs = get_subscribers()
        if not subs:
            print("No subscribers yet. Add with: python subscribers.py add <email>")
        else:
            print(f"{len(subs)} subscriber(s):\n")
            for i, s in enumerate(subs, 1):
                print(f"  {i}. {s}")

    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Usage: python subscribers.py add <email> [email2...]")
            return
        for email in sys.argv[2:]:
            ok, msg = add_subscriber(email)
            print(f"  {msg}")

    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("Usage: python subscribers.py remove <email>")
            return
        ok, msg = remove_subscriber(sys.argv[2])
        print(f"  {msg}")

    elif cmd == "import-env":
        print("Importing subscribers from .env...")
        added = import_from_env()
        print(f"\nDone. {added} new subscriber(s) imported.")

    elif cmd == "count":
        print(f"{len(get_subscribers())} subscriber(s)")

    else:
        print(f"Unknown command: {cmd}")
        print("Run 'python subscribers.py' for help.")


if __name__ == "__main__":
    main()
