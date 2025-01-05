import curses
import requests
import warnings
import logging
from urllib.parse import urlparse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    filename="qbtui.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class QBittorrentTUI:
    """
    A terminal-based user interface (TUI) for managing qBittorrent
    via its Web API. Supports:
      - Logging in with username/password
      - Removing a selected tracker from multiple torrents
      - Scrollable UI for choosing a tracker
      - Basic error handling and logging
      - Text-based progress bar and line wrapping in the curses UI
    """

    def __init__(self):
        """
        Initialize a requests.Session for communication with qBittorrent,
        ignoring SSL errors, and prepare placeholders for user credentials.
        """
        self.session = requests.Session()
        self.session.verify = False  # Ignore SSL certificate verification
        self.url = ""
        self.username = ""
        self.password = ""

    def prompt(self, stdscr, prompt_text):
        """
        Display a prompt to the user, capture input in echo mode, and return it.

        :param stdscr: The main curses screen.
        :param prompt_text: The text to display as a prompt.
        :return: The user-input string.
        """
        curses.echo()
        self.safe_addstr(stdscr, prompt_text, wrap=False, start_newline=False)
        user_input = stdscr.getstr().decode("utf-8").strip()
        curses.noecho()
        return user_input

    import curses

    import curses

    def password_prompt(self, stdscr, prompt_text):
        """
        Safely read a password without echoing it back in plain text.
        Instead, display '*' characters.

        :param stdscr: The main curses screen.
        :param prompt_text: The text to display as a prompt.
        :return: The user-input password string.
        """
        try:
            curses.noecho()  # Disable echoing input
            self.safe_addstr(stdscr, prompt_text, wrap=False, start_newline=False)
            password = ""
            
            while True:
                char = stdscr.getch()
                
                if char in (curses.KEY_ENTER, 10, 13):
                    break
                elif char in (curses.KEY_BACKSPACE, 127):
                    if password:
                        password = password[:-1]
                        y, x = stdscr.getyx()
                        if x > 0:
                            stdscr.move(y, x - 1)
                            stdscr.addch(" ")
                            stdscr.move(y, x - 1)
                elif 32 <= char <= 126:
                    password += chr(char)
                    stdscr.addstr("*")
                else:
                    continue
            
            return password.strip()
        
        finally:
            curses.echo()  # Ensure echo is restored

    def safe_addstr(self, stdscr, text, wrap=True, start_newline=True):
        """
        Safely add strings to the curses screen, handling line wrapping
        and preventing any width or height overflows.

        :param stdscr: The main curses screen.
        :param text: The text to display (can contain multiple lines).
        :param wrap: If True, wrap lines that exceed screen width.
        :param start_newline: If True, add a newline after writing the text.
        """
        height, width = stdscr.getmaxyx()

        # Split into lines first (to handle embedded newlines)
        for original_line in text.splitlines():
            line = original_line
            if wrap:
                # Wrap the line manually if it's longer than screen width
                while len(line) > width:
                    segment = line[:width]
                    try:
                        stdscr.addstr(segment + "\n")
                    except curses.error:
                        pass
                    line = line[width:]
                # Print the remainder of the line
                try:
                    stdscr.addstr(line + "\n")
                except curses.error:
                    pass
            else:
                # Truncate the line if it exceeds screen width, and print
                if len(line) > width:
                    line = line[:width - 1]
                try:
                    stdscr.addstr(line)
                except curses.error:
                    pass

        if start_newline:
            try:
                stdscr.addstr("\n")
            except curses.error:
                pass

        stdscr.refresh()

    def draw_progress_bar(self, stdscr, current, total, message="", bar_length=40):
        """
        Draw a text-based progress bar at the bottom of the screen.

        :param stdscr: The main curses screen.
        :param current: The current iteration (int).
        :param total: The total iterations (int).
        :param message: An optional message to display above the progress bar.
        :param bar_length: The total character length of the progress bar.
        """
        height, width = stdscr.getmaxyx()

        # Calculate percentage
        percentage = 0
        if total != 0:
            percentage = float(current) / float(total)
        filled_length = int(bar_length * percentage)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        percent_text = f"{int(percentage * 100)}%"

        # We will draw the progress bar near the bottom of the screen
        bar_y = height - 3

        # Clear the lines to avoid overlapping text
        for clear_y in range(bar_y, height):
            stdscr.move(clear_y, 0)
            stdscr.clrtoeol()

        # Write the optional message
        stdscr.move(bar_y, 0)
        truncated_message = message[:width - 1] if len(message) > width - 1 else message
        stdscr.addstr(truncated_message)

        # Draw progress bar
        bar_line = f"[{bar}] {percent_text}"
        bar_line_y = bar_y + 1
        stdscr.move(bar_line_y, 0)
        bar_line_display = bar_line[:width - 1]  # Truncate if needed
        stdscr.addstr(bar_line_display)

        stdscr.refresh()

    def validate_url(self, input_url):
        """
        Validate and (lightly) normalize the qBittorrent URL.
        If the user did not provide a scheme (http/https), assume http.

        :param input_url: The URL string provided by the user.
        :return: A normalized URL string, or an empty string if invalid.
        """
        if not input_url:
            return ""

        parsed = urlparse(input_url)
        # If scheme is missing, default to http
        if not parsed.scheme:
            input_url = "http://" + input_url

        # Strip trailing slashes
        return input_url.rstrip("/")

    def login(self, stdscr):
        """
        Prompt the user for qBittorrent Web credentials and attempt to log in.
        If successful, returns True. Otherwise, logs and notifies the user,
        then returns False.

        :param stdscr: The main curses screen.
        :return: Boolean indicating login success or failure.
        """
        stdscr.clear()
        self.safe_addstr(stdscr, "=== qBittorrent Login ===")

        # Prompt for URL, validate and store it.
        while True:
            user_url = self.prompt(stdscr, "Enter qBittorrent Web URL (e.g., http://localhost:8080): ")
            self.url = self.validate_url(user_url)
            if self.url:
                break
            else:
                self.safe_addstr(stdscr, "Invalid URL. Please try again.\n")

        # Prompt for Username
        self.username = self.prompt(stdscr, "Enter Username: ")

        # Prompt for Password
        self.password = self.password_prompt(stdscr, "Enter Password: ")

        # Perform login
        try:
            headers = {'Referer': self.url}
            response = self.session.post(
                f"{self.url}/api/v2/auth/login",
                data={"username": self.username, "password": self.password},
                headers=headers
            )

            if response.status_code == 200:
                logging.info("Login successful.")
                self.safe_addstr(stdscr, "Login successful! Press any key to continue...")
                stdscr.getch()
                return True
            else:
                logging.error(f"Login failed! Status: {response.status_code}, Response: {response.text}")
                self.safe_addstr(
                    stdscr,
                    f"Login failed (HTTP {response.status_code}). "
                    f"Check credentials and URL.\nPress any key to exit."
                )
                stdscr.getch()
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Error connecting to qBittorrent: {e}")
            self.safe_addstr(
                stdscr,
                f"Error connecting to qBittorrent: {e}\nPress any key to exit."
            )
            stdscr.getch()
            return False

    def get_torrent_trackers(self, torrent_hash):
        """
        Fetch and return trackers for a specific torrent via the Web API.

        :param torrent_hash: The unique hash of the torrent.
        :return: A list of trackers or an empty list on failure.
        """
        try:
            response = self.session.get(
                f"{self.url}/api/v2/torrents/trackers?hash={torrent_hash}"
            )
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching trackers for {torrent_hash}: {e}")
        return []

    def scrollable_select(self, stdscr, items, title="Select an item"):
        """
        Present a scrollable list of items. The user can scroll with arrow keys,
        PageUp/PageDown, Home/End, and press Enter to select an item or 'q'/ESC to cancel.

        :param stdscr: The main curses screen.
        :param items: A list of strings to display (one per line).
        :param title: A title to display at the top of the screen.
        :return: The index of the selected item, or -1 if canceled.
        """
        curses.curs_set(0)  # Hide the cursor
        height, width = stdscr.getmaxyx()

        # If there's no content, bail out
        if not items:
            return -1

        selected_idx = 0  # Currently highlighted index
        top_line = 0      # Index of the topmost visible line

        while True:
            stdscr.clear()
            # Draw title at the top
            self.safe_addstr(stdscr, f"=== {title} ===\n")

            # Calculate how many lines we can show
            # (we subtract a few lines for the title and spacing)
            max_lines = height - 4

            # Determine the range of items to display
            visible_items = items[top_line:top_line + max_lines]

            # Display each visible item
            for i, line in enumerate(visible_items):
                actual_idx = top_line + i
                if actual_idx == selected_idx:
                    # Highlight this line
                    stdscr.attron(curses.A_REVERSE)
                    self.safe_addstr(stdscr, line, wrap=False)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    self.safe_addstr(stdscr, line, wrap=False)
            
            # Additional help prompt
            help_line = (
                "[UP/DOWN] scroll, [PgUp/PgDn] faster scroll, "
                "[Home/End], [Enter] select, [q] or [ESC] to cancel."
            )
            self.safe_addstr(stdscr, help_line, wrap=False, start_newline=True)

            stdscr.refresh()

            # Get user input
            key = stdscr.getch()

            if key in (ord('q'), 27):  # 27 is ESC
                # User canceled
                return -1
            elif key in (curses.KEY_ENTER, 10, 13):
                # User pressed Enter: return the selected index
                return selected_idx
            elif key in (curses.KEY_UP, ord('k')):
                # Move selection up
                selected_idx = max(0, selected_idx - 1)
                # Adjust top_line if needed
                if selected_idx < top_line:
                    top_line = selected_idx
            elif key in (curses.KEY_DOWN, ord('j')):
                # Move selection down
                selected_idx = min(len(items) - 1, selected_idx + 1)
                # If selection goes past bottom visible line, scroll
                if selected_idx >= top_line + max_lines:
                    top_line = selected_idx - max_lines + 1
            elif key == curses.KEY_PPAGE:  # Page Up
                selected_idx = max(0, selected_idx - max_lines)
                if selected_idx < top_line:
                    top_line = selected_idx
            elif key == curses.KEY_NPAGE:  # Page Down
                selected_idx = min(len(items) - 1, selected_idx + max_lines)
                if selected_idx >= top_line + max_lines:
                    top_line = selected_idx - max_lines + 1
            elif key == curses.KEY_HOME:
                selected_idx = 0
                top_line = 0
            elif key == curses.KEY_END:
                selected_idx = len(items) - 1
                # Position top_line so the last item is visible
                top_line = max(0, len(items) - max_lines)

    def remove_tracker(self, stdscr):
        """
        Aggregate all trackers from all torrents. Let the user select a tracker to remove
        in a scrollable list, confirm the operation, then remove that tracker from every
        torrent in which it appears.

        :param stdscr: The main curses screen.
        """
        stdscr.clear()
        self.safe_addstr(stdscr, "=== Remove a Tracker ===")

        # Fetch all torrent info
        try:
            response = self.session.get(f"{self.url}/api/v2/torrents/info")
            if response.status_code != 200:
                logging.error(
                    f"Error fetching torrents: Status {response.status_code}, "
                    f"Response: {response.text}"
                )
                self.safe_addstr(
                    stdscr,
                    f"Error fetching torrents: HTTP {response.status_code}\n"
                    f"{response.text}\nPress any key to return to main menu..."
                )
                stdscr.getch()
                return

            torrents = response.json()
            total_torrents = len(torrents)
            self.safe_addstr(stdscr, f"Total torrents found: {total_torrents}")

            if total_torrents == 0:
                self.safe_addstr(stdscr, "No torrents found. Press any key to return...")
                stdscr.getch()
                return

            # Aggregate trackers for each torrent
            tracker_map = {}
            for idx, torrent in enumerate(torrents, start=1):
                # Show progress info for gathering tracker data
                message = f"Gathering trackers for torrent {idx}/{total_torrents}: {torrent['name']}"
                self.draw_progress_bar(stdscr, idx, total_torrents, message=message)

                torrent_trackers = self.get_torrent_trackers(torrent["hash"])
                for tracker in torrent_trackers:
                    tracker_url = tracker["url"]
                    if tracker_url not in tracker_map:
                        tracker_map[tracker_url] = []
                    tracker_map[tracker_url].append(torrent["hash"])

            # Clear progress bar area before the next step
            stdscr.clear()

            if not tracker_map:
                self.safe_addstr(stdscr, "No trackers found across all torrents.")
                self.safe_addstr(stdscr, "Press any key to return to the main menu...")
                stdscr.getch()
                return

            # Prepare a list of trackers for scrollable selection
            trackers = sorted(tracker_map.keys())  # Sort for consistent display
            tracker_lines = []
            for i, tracker_url in enumerate(trackers, start=1):
                line = f"{i}. {tracker_url} - Found in {len(tracker_map[tracker_url])} torrents"
                tracker_lines.append(line)

            # Use scrollable_select to get user's choice
            choice_idx = self.scrollable_select(stdscr, tracker_lines, title="Remove a Tracker")
            if choice_idx < 0:
                # User canceled
                self.safe_addstr(stdscr, "Operation canceled. Press any key to return...")
                stdscr.getch()
                return

            # Now we have the selected index
            selected_tracker = trackers[choice_idx]
            associated_torrents = tracker_map[selected_tracker]
            stdscr.clear()
            self.safe_addstr(
                stdscr,
                f"Selected tracker:\n{selected_tracker}\n\n"
                f"It appears in {len(associated_torrents)} torrents.\n"
            )

            confirmation = self.prompt(
                stdscr,
                "Do you want to remove this tracker from all associated torrents? (yes/no): "
            ).lower()
            if confirmation != "yes":
                logging.info("Tracker removal operation canceled by user.")
                self.safe_addstr(stdscr, "Operation canceled. Press any key to return...")
                stdscr.getch()
                return

            # Remove the tracker from all associated torrents
            total_associated = len(associated_torrents)
            stdscr.clear()
            for idx, torrent_hash in enumerate(associated_torrents, start=1):
                message = f"Removing tracker from torrent {idx}/{total_associated}"
                self.draw_progress_bar(stdscr, idx, total_associated, message=message)

                try:
                    remove_resp = self.session.post(
                        f"{self.url}/api/v2/torrents/removeTrackers",
                        data={"hash": torrent_hash, "urls": selected_tracker}
                    )
                    if remove_resp.status_code == 200:
                        logging.info(f"Successfully removed tracker {selected_tracker} from {torrent_hash}")
                    else:
                        logging.error(
                            f"Failed to remove tracker {selected_tracker} from {torrent_hash}. "
                            f"Status: {remove_resp.status_code}, Response: {remove_resp.text}"
                        )
                except requests.exceptions.RequestException as e:
                    logging.error(f"Network error removing tracker from {torrent_hash}: {e}")

            # Clear final progress bar and notify user
            stdscr.clear()
            self.safe_addstr(
                stdscr,
                f"Tracker '{selected_tracker}' removed from all associated torrents."
            )
            self.safe_addstr(stdscr, "Press any key to return to the main menu...")
            stdscr.getch()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error removing tracker: {e}")
            self.safe_addstr(
                stdscr,
                f"Error removing tracker: {e}\nPress any key to return."
            )
            stdscr.getch()

    def main_menu(self, stdscr):
        """
        Display the main menu, handle user input, and call the appropriate
        methods based on the user's choice.

        :param stdscr: The main curses screen.
        """
        stdscr.clear()
        self.safe_addstr(stdscr, "=== qBittorrent TUI ===")
        self.safe_addstr(stdscr, "1. Remove a Tracker")
        self.safe_addstr(stdscr, "2. Exit")
        self.safe_addstr(stdscr, "Select an option: ", wrap=False, start_newline=False)

        curses.echo()
        choice = stdscr.getstr().decode("utf-8").strip()
        curses.noecho()

        if choice == '1':
            self.remove_tracker(stdscr)
        elif choice == '2':
            # Exit gracefully
            logging.info("User selected Exit.")
            stdscr.clear()
            self.safe_addstr(stdscr, "Exiting... Press any key.")
            stdscr.getch()
            exit()
        else:
            # Invalid choice; show the menu again
            self.safe_addstr(stdscr, "Invalid selection. Press any key to try again...")
            stdscr.getch()

    def run(self, stdscr):
        """
        The main entry point for the TUI after curses.wrapper is called.
        Attempts to log in; if successful, loops the main menu until exit.

        :param stdscr: The main curses screen.
        """
        # Attempt login first
        if self.login(stdscr):
            while True:
                self.main_menu(stdscr)

def main():
    tui = QBittorrentTUI()
    curses.wrapper(tui.run)

if __name__ == "__main__":
    main()
