import argparse
import sys
import getpass
import time
from roblox_multi.storage import ProfileStore
from roblox_multi.auth import validate_cookie, get_user_info, refresh_auth_ticket
from roblox_multi.mutex import unlock_mutex, is_mutex_active
from roblox_multi.process import launch_roblox


def cmd_add(args):
    store = ProfileStore()
    name = args.name.strip()
    
    if store.has_profile(name) and not args.force:
        print(f"Profile '{name}' already exists. Use --force to overwrite.")
        return 1
        
    cookie = args.cookie
    if not cookie:
        cookie = getpass.getpass("Paste .ROBLOSECURITY cookie: ").strip()
        
    if not cookie:
        print("Error: cookie cannot be empty.")
        return 1
        
    # strip standard warning prefix if copied straight from devtools
    if "WARNING:-" in cookie:
        cookie = cookie.split("WARNING:-")[-1].lstrip("_")
        
    print("Validating cookie with Roblox API...")
    user = validate_cookie(cookie)
    if not user:
        print("Failed: cookie appears invalid or expired.")
        return 1
        
    store.save_profile(name, cookie, user_id=user["id"], username=user["name"])
    print(f"Saved profile '{name}' (User: {user['name']}, ID: {user['id']})")
    return 0


def cmd_list(args):
    store = ProfileStore()
    profiles = store.list_profiles()
    if not profiles:
        print("No profiles saved yet. Add one with: roblox-multi add <name>")
        return 0
        
    print(f"Found {len(profiles)} profile(s):")
    for p in profiles:
        uname = p.get("username", "unknown")
        uid = p.get("user_id", "-")
        status = ""
        if args.check:
            # quick probe so we know if cookies went stale without launching
            valid = validate_cookie(p["cookie"]) is not None
            status = " [OK]" if valid else " [EXPIRED]"
        print(f" - {p['name']:<16} (User: {uname:<16} ID: {uid}){status}")
    return 0


def cmd_remove(args):
    store = ProfileStore()
    if not store.has_profile(args.name):
        print(f"Profile '{args.name}' not found.")
        return 1
    store.delete_profile(args.name)
    print(f"Removed profile '{args.name}'.")
    return 0


def cmd_unlock(args):
    """Manual mutex release if background cleaner was terminated."""
    print("Attempting to clear ROBLOX_singletonMutex...")
    if unlock_mutex(persistent=args.persist):
        if args.persist:
            print("Mutex handle held open. Press Ctrl+C to release.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nReleased mutex.")
        else:
            print("Mutex handle closed successfully.")
        return 0
    print("Failed to handle mutex. Is Roblox running as admin?")
    return 1


def cmd_launch(args):
    store = ProfileStore()
    profile = store.get_profile(args.name)
    if not profile:
        print(f"Profile '{args.name}' not found. Check 'roblox-multi list'.")
        return 1
        
    # TODO: handle deep-link join URLs directly instead of placeId/jobId flags
    if not args.no_mutex:
        ok = unlock_mutex()
        if not ok:
            print("Warning: could not release mutex. If another instance is running, launch may focus that window instead.")
            
    cookie = profile["cookie"]
    print(f"Fetching auth ticket for '{profile.get('username', args.name)}'...")
    ticket = refresh_auth_ticket(cookie)
    if not ticket:
        print("Error: could not generate authentication ticket. Cookie might have expired or hit CSRF challenge.")
        return 1
        
    # print(f"DEBUG: ticket={ticket[:10]}...")
    print(f"Launching client instance...")
    proc = launch_roblox(
        auth_ticket=ticket,
        place_id=args.place_id,
        job_id=args.job_id,
        browser_tracker_id=args.tracker_id
    )
    if proc:
        print(f"Roblox started (PID: {proc.pid})")
        if args.wait:
            print("Waiting for process to exit...")
            proc.wait()
        return 0
    else:
        print("Failed to spawn Roblox process.")
        return 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="roblox-multi",
        description="Manage multiple Roblox profiles and run parallel instances without mutex blocks"
    )
    sub = parser.add_subparsers(dest="command", help="command to run")
    
    # add
    p_add = sub.add_parser("add", help="save a new account profile")
    p_add.add_argument("name", help="local label for this profile")
    p_add.add_argument("--cookie", help="raw .ROBLOSECURITY cookie value (prompts if omitted)")
    p_add.add_argument("-f", "--force", action="store_true", help="overwrite existing profile")
    
    # list
    p_list = sub.add_parser("list", aliases=["ls"], help="list saved profiles")
    p_list.add_argument("-c", "--check", action="store_true", help="validate each stored cookie online")
    
    # remove
    p_rm = sub.add_parser("remove", aliases=["rm"], help="delete a saved profile")
    p_rm.add_argument("name", help="name of profile to remove")
    
    # unlock
    p_un = sub.add_parser("unlock", help="manually close or hold the singleton mutex")
    p_un.add_argument("--persist", action="store_true", help="keep script running to hold mutex ownership")
    
    # launch
    p_launch = sub.add_parser("launch", aliases=["run"], help="launch client instance under profile")
    p_launch.add_argument("name", help="profile name to launch")
    p_launch.add_argument("-p", "--place-id", type=int, default=None, help="place ID to join immediately")
    p_launch.add_argument("-j", "--job-id", default=None, help="specific server job ID")
    p_launch.add_argument("-t", "--tracker-id", default=None, help="browser tracker ID for analytics/joins")
    p_launch.add_argument("-w", "--wait", action="store_true", help="block until client process exits")
    p_launch.add_argument("--no-mutex", action="store_true", help="skip mutex patch before launch")
    
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 0
        
    handlers = {
        "add": cmd_add,
        "list": cmd_list,
        "ls": cmd_list,
        "remove": cmd_remove,
        "rm": cmd_remove,
        "unlock": cmd_unlock,
        "launch": cmd_launch,
        "run": cmd_launch,
    }
    
    fn = handlers.get(args.command)
    if fn:
        return fn(args)
    parser.print_help()
    return 1
