#!/usr/bin/env python3
"""Interactive DNS Manager TUI for Namecheap domains."""

import threading

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)

from namecheap import Namecheap
from namecheap.models import DNSRecord


class ConfirmModal(ModalScreen):
    """Simple confirmation modal."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+enter", "confirm", "Confirm", show=True),
        Binding("ctrl+q", "quit", "Quit App", show=True),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    CSS = """
    ConfirmModal {
        align: center middle;
    }
    
    #confirm-dialog {
        background: $surface;
        border: thick $error;
        padding: 2 4;
        width: 70;
        height: auto;
        max-height: 12;
    }
    
    .confirm-message {
        text-align: center;
        margin-bottom: 2;
        color: $text;
        text-style: bold;
    }
    
    .button-row {
        align: center middle;
        height: 3;
    }
    
    .button-row Button {
        margin: 0 2;
        width: 16;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Label(self.message, classes="confirm-message")
            with Horizontal(classes="button-row"):
                yield Button("Confirm", variant="error", id="btn-confirm")
                yield Button("Cancel", variant="default", id="btn-cancel")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        """Confirm action."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel action."""
        self.dismiss(False)

    def action_quit(self) -> None:
        """Quit the entire application."""
        self.app.exit()


class AddRecordModal(ModalScreen):
    """Modal dialog for adding DNS records."""

    BINDINGS = [
        Binding("escape", "escape", "Cancel", show=True),
        Binding("ctrl+q", "quit", "Quit App", show=True),
        Binding("ctrl+enter", "submit", "Save", show=True),
        Binding("left", "focus_previous", "Prev Field", show=False),
        Binding("right", "focus_next", "Next Field", show=False),
    ]

    def __init__(self, domain: str, record: DNSRecord | None = None) -> None:
        super().__init__()
        self.domain = domain
        self.editing_record = record

    CSS = """
    AddRecordModal {
        align: center middle;
    }
    
    #dialog {
        background: $surface;
        border: solid $primary;
        width: 90%;
        height: 90%;
        max-width: 80;
        max-height: 35;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        color: $primary;
        height: 3;
        padding: 1;
        dock: top;
    }
    
    #form-scroll {
        padding: 1;
    }
    
    .field-group {
        height: auto;
        margin-bottom: 1;
    }
    
    .field-group Label {
        height: 1;
    }
    
    .field-group Input {
        height: 3;
        width: 100%;
    }
    
    .field-group Select {
        height: 3;
        width: 100%;
    }
    
    .button-row {
        height: 4;
        dock: bottom;
        align: center middle;
        background: $surface;
        border-top: solid $primary;
    }
    
    .button-row Button {
        width: 20;
        height: 3;
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            title = (
                f"Edit DNS Record for {self.domain}"
                if self.editing_record
                else f"Add DNS Record to {self.domain}"
            )
            yield Label(title, classes="title")

            with ScrollableContainer(id="form-scroll"):
                with Vertical(classes="field-group"):
                    yield Label("Record Type:")
                    initial_type = self.editing_record.type if self.editing_record else "A"
                    yield Select(
                        [
                            ("A - IPv4 Address", "A"),
                            ("AAAA - IPv6 Address", "AAAA"),
                            ("CNAME - Canonical Name", "CNAME"),
                            ("MX - Mail Exchange", "MX"),
                            ("TXT - Text Record", "TXT"),
                            ("NS - Name Server", "NS"),
                            ("URL - URL Redirect (302)", "URL"),
                            ("URL301 - URL Redirect (301)", "URL301"),
                            ("FRAME - URL Frame", "FRAME"),
                        ],
                        id="record-type",
                        value=initial_type,
                    )

                with Vertical(classes="field-group"):
                    yield Label("Name:")
                    initial_name = self.editing_record.name if self.editing_record else "@"
                    yield Input(
                        placeholder="@ for root or subdomain",
                        id="record-name",
                        value=initial_name,
                    )

                with Vertical(classes="field-group"):
                    yield Label("Value:")
                    initial_value = self.editing_record.value if self.editing_record else ""
                    yield Input(
                        placeholder="Enter value based on record type",
                        id="record-value",
                        value=initial_value,
                    )

                with Vertical(classes="field-group"):
                    yield Label("TTL (seconds):")
                    initial_ttl = str(self.editing_record.ttl) if self.editing_record else "1800"
                    yield Input(placeholder="1800", id="record-ttl", value=initial_ttl)

                with Vertical(classes="field-group", id="priority-group"):
                    yield Label("Priority:")
                    initial_priority = (
                        str(self.editing_record.priority)
                        if self.editing_record and self.editing_record.priority
                        else ""
                    )
                    yield Input(placeholder="10", id="record-priority", value=initial_priority)

            with Horizontal(classes="button-row"):
                button_text = "Save Changes" if self.editing_record else "Add Record"
                yield Button(button_text, variant="primary", id="btn-add")
                yield Button("Cancel", id="btn-cancel")

        yield Footer()

    def on_mount(self) -> None:
        """Focus on record type selector when modal opens."""
        self.query_one("#record-type", Select).focus()
        # Show/hide priority field based on initial type
        priority_group = self.query_one("#priority-group")
        if self.editing_record and self.editing_record.type == "MX":
            priority_group.display = True
        else:
            priority_group.display = False

    def on_select_changed(self, event: Select.Changed) -> None:
        """Update form based on record type."""
        if event.select.id == "record-type":
            priority_group = self.query_one("#priority-group")
            value_input = self.query_one("#record-value", Input)

            # Show/hide priority field for MX records
            priority_group.display = event.value == "MX"

            # Update placeholder based on type
            placeholders = {
                "A": "192.0.2.1",
                "AAAA": "2001:db8::1",
                "CNAME": "target.example.com",
                "MX": "mail.example.com",
                "TXT": "v=spf1 include:_spf.example.com ~all",
                "NS": "ns1.example.com",
                "URL": "https://example.com",
                "URL301": "https://example.com",
                "FRAME": "https://example.com",
            }
            value_input.placeholder = placeholders.get(event.value, "Enter value")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-add":
            try:
                # Collect values
                record_type = self.query_one("#record-type", Select).value
                name = self.query_one("#record-name", Input).value or "@"
                value = self.query_one("#record-value", Input).value
                ttl_str = self.query_one("#record-ttl", Input).value or "1800"
                ttl = max(60, min(86400, int(ttl_str)))

                priority = None
                if record_type == "MX":
                    priority_str = self.query_one("#record-priority", Input).value
                    priority = int(priority_str) if priority_str else 10

                if not value:
                    self.app.update_status("Error: Value is required")
                    return

                # Create record
                record = DNSRecord(
                    name=name, type=record_type, value=value, ttl=ttl, priority=priority
                )

                # Dismiss with the record
                self.dismiss(record)

            except ValueError as e:
                self.app.update_status(f"Error: Invalid input - {e}")
        else:
            self.dismiss(None)

    def action_escape(self) -> None:
        """Handle escape key - blur focused widget or dismiss modal."""
        # Check if any widget has focus
        focused = self.focused
        if focused and not isinstance(focused, Button):
            # Blur the focused widget (dropdown or input)
            self.set_focus(None)
        else:
            # No input focused, dismiss modal
            self.dismiss(None)

    def action_quit(self) -> None:
        """Quit the entire application."""
        self.app.exit()

    def action_submit(self) -> None:
        """Submit the form (Ctrl+Enter to add record)."""
        self.on_button_pressed(Button.Pressed(self.query_one("#btn-add")))

    def action_focus_previous(self) -> None:
        """Focus previous field with left arrow."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Focus next field with right arrow."""
        self.focus_next()


class DNSManagerApp(App):
    """DNS Manager TUI Application."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    #domain-select {
        width: 100%;
        margin: 1 2;
    }
    
    #records-table {
        margin: 1 2;
        height: 80%;
    }
    
    #status {
        dock: bottom;
        height: 3;
        padding: 1 2;
        background: $panel;
        border-top: solid $primary;
    }
    
    .domain-info {
        margin: 0 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True, priority=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("a", "add_record", "Add Record", show=True),
        Binding("e", "edit_record", "Edit", show=True),
        Binding("d", "delete_record", "Delete", show=True),
        Binding("escape", "escape", "Unfocus", show=True),
        Binding("left", "focus_previous", "Prev", show=False),
        Binding("right", "focus_next", "Next", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.nc = Namecheap()
        self.domains = []
        self.current_domain = None
        self.records = []
        self._threads = []

    def compose(self) -> ComposeResult:
        yield Header()

        yield Label("Select Domain:")
        yield Select([], id="domain-select")
        yield Static("", classes="domain-info", id="domain-info")

        yield DataTable(id="records-table")

        yield Static("Ready", id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize when app starts."""
        # Setup table
        table = self.query_one("#records-table", DataTable)
        table.add_columns("Type", "Name", "Value", "TTL", "Priority")
        table.cursor_type = "row"

        # Load domains in background
        self.load_domains_async()

    def load_domains_async(self) -> None:
        """Load domains in a thread."""

        def load() -> None:
            try:
                domains = self.nc.domains.list()
                if self.is_running:
                    self.call_from_thread(self.update_domains, domains)
            except Exception as e:
                if self.is_running:
                    self.call_from_thread(self.update_status, f"Error: {e}")

        thread = threading.Thread(target=load, daemon=True)
        self._threads.append(thread)
        thread.start()

    def update_domains(self, domains) -> None:
        """Update domain selector."""
        self.domains = domains
        if domains:
            select = self.query_one("#domain-select", Select)
            select.set_options([(d.name, d.name) for d in domains])
            self.update_status(f"Loaded {len(domains)} domains")
        else:
            self.update_status("No domains found")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle domain selection."""
        if event.select.id == "domain-select" and event.value:
            self.current_domain = event.value
            # Update domain info
            domain = next((d for d in self.domains if d.name == event.value), None)
            if domain:
                info = f"Expires: {domain.expires.strftime('%Y-%m-%d')} | "
                info += f"Auto-renew: {'Yes' if domain.auto_renew else 'No'} | "
                info += f"Locked: {'Yes' if domain.is_locked else 'No'}"
                self.query_one("#domain-info", Static).update(info)
            self.load_records_async()

    def load_records_async(self) -> None:
        """Load DNS records in a thread."""

        def load() -> None:
            try:
                records = self.nc.dns.get(self.current_domain)
                if self.is_running:
                    self.call_from_thread(self.update_records, records)
            except Exception as e:
                if self.is_running:
                    self.call_from_thread(self.update_status, f"Error: {e}")

        thread = threading.Thread(target=load, daemon=True)
        self._threads.append(thread)
        thread.start()

    def update_records(self, records) -> None:
        """Update records table."""
        self.records = list(records)
        table = self.query_one("#records-table", DataTable)
        table.clear()

        for record in self.records:
            table.add_row(
                record.type,
                record.name,
                record.value[:50] + "..." if len(record.value) > 50 else record.value,
                str(record.ttl),
                str(record.priority) if record.priority else "-",
            )

        self.update_status(f"Loaded {len(self.records)} records for {self.current_domain}")

    def action_refresh(self) -> None:
        """Refresh records."""
        if self.current_domain:
            self.load_records_async()

    def action_add_record(self) -> None:
        """Show add record modal."""
        if not self.current_domain:
            self.update_status("Please select a domain first")
            return

        def handle_result(result) -> None:
            """Handle the modal result."""
            if result:
                self.update_status(f"Adding {result.type} record...")

                def add() -> None:
                    try:
                        # Build all records including the new one
                        self.records.append(result)
                        builder = self.nc.dns.builder()

                        for record in self.records:
                            if record.type == "A":
                                builder.a(record.name, record.value, ttl=record.ttl)
                            elif record.type == "AAAA":
                                builder.aaaa(record.name, record.value, ttl=record.ttl)
                            elif record.type == "CNAME":
                                builder.cname(record.name, record.value, ttl=record.ttl)
                            elif record.type == "MX":
                                builder.mx(
                                    record.name,
                                    record.value,
                                    priority=record.priority or 10,
                                    ttl=record.ttl,
                                )
                            elif record.type == "TXT":
                                builder.txt(record.name, record.value, ttl=record.ttl)
                            elif record.type == "NS":
                                builder.ns(record.name, record.value, ttl=record.ttl)
                            elif record.type == "URL":
                                # URL type is 302 redirect
                                builder.url(
                                    record.name,
                                    record.value,
                                    redirect_type="301",
                                    ttl=record.ttl,
                                )
                                builder._records[
                                    -1
                                ].type = "URL"  # Override to use URL instead of URL301
                            elif record.type == "URL301":
                                builder.url(
                                    record.name,
                                    record.value,
                                    redirect_type="301",
                                    ttl=record.ttl,
                                )
                            elif record.type == "FRAME":
                                builder.url(
                                    record.name,
                                    record.value,
                                    redirect_type="frame",
                                    ttl=record.ttl,
                                )

                        # Save to Namecheap
                        self.nc.dns.set(self.current_domain, builder)

                        if self.is_running:
                            self.call_from_thread(
                                self.update_status,
                                f"✅ Added {result.type} record successfully!",
                            )
                            # Reload to get fresh data
                            self.call_from_thread(self.load_records_async)
                    except Exception as e:
                        if self.is_running:
                            self.call_from_thread(
                                self.update_status, f"❌ Error adding record: {e}"
                            )
                            # Remove the failed record
                            self.records.remove(result)

                thread = threading.Thread(target=add, daemon=True)
                self._threads.append(thread)
                thread.start()

        self.push_screen(AddRecordModal(self.current_domain), handle_result)

    def action_edit_record(self) -> None:
        """Edit selected record."""
        table = self.query_one("#records-table", DataTable)
        cursor_coordinate = table.cursor_coordinate
        if cursor_coordinate and cursor_coordinate.row < len(self.records):
            record = self.records[cursor_coordinate.row]
            original_index = cursor_coordinate.row

            def handle_result(result) -> None:
                """Handle the modal result."""
                if result:
                    self.update_status(f"Saving changes to {result.type} record...")

                    def save() -> None:
                        try:
                            # Replace the record at the original index
                            self.records[original_index] = result

                            # Build all records
                            builder = self.nc.dns.builder()

                            for rec in self.records:
                                if rec.type == "A":
                                    builder.a(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "AAAA":
                                    builder.aaaa(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "CNAME":
                                    builder.cname(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "MX":
                                    builder.mx(
                                        rec.name,
                                        rec.value,
                                        priority=rec.priority or 10,
                                        ttl=rec.ttl,
                                    )
                                elif rec.type == "TXT":
                                    builder.txt(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "NS":
                                    builder.ns(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "URL":
                                    # URL type is 302 redirect
                                    builder.url(
                                        rec.name,
                                        rec.value,
                                        redirect_type="301",
                                        ttl=rec.ttl,
                                    )
                                    builder._records[
                                        -1
                                    ].type = "URL"  # Override to use URL instead of URL301
                                elif rec.type == "URL301":
                                    builder.url(
                                        rec.name,
                                        rec.value,
                                        redirect_type="301",
                                        ttl=rec.ttl,
                                    )
                                elif rec.type == "FRAME":
                                    builder.url(
                                        rec.name,
                                        rec.value,
                                        redirect_type="frame",
                                        ttl=rec.ttl,
                                    )

                            # Save to Namecheap
                            self.nc.dns.set(self.current_domain, builder)

                            if self.is_running:
                                self.call_from_thread(
                                    self.update_status,
                                    f"✅ Updated {result.type} record successfully!",
                                )
                                # Reload to get fresh data
                                self.call_from_thread(self.load_records_async)
                        except Exception as e:
                            if self.is_running:
                                self.call_from_thread(
                                    self.update_status, f"❌ Error updating record: {e}"
                                )
                                # Restore original record
                                self.records[original_index] = record

                    thread = threading.Thread(target=save, daemon=True)
                    self._threads.append(thread)
                    thread.start()

            self.push_screen(AddRecordModal(self.current_domain, record), handle_result)

    def action_delete_record(self) -> None:
        """Delete selected record."""
        table = self.query_one("#records-table", DataTable)
        # Get the current cursor coordinate
        cursor_coordinate = table.cursor_coordinate
        if cursor_coordinate and cursor_coordinate.row < len(self.records):
            record = self.records[cursor_coordinate.row]

            def handle_confirm(confirmed: bool) -> None:
                """Handle delete confirmation."""
                if confirmed:
                    self.update_status(f"Deleting {record.type} record '{record.name}'...")

                    def delete() -> None:
                        try:
                            # Remove from our records list
                            self.records.remove(record)

                            # Build remaining records
                            builder = self.nc.dns.builder()
                            for rec in self.records:
                                if rec.type == "A":
                                    builder.a(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "AAAA":
                                    builder.aaaa(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "CNAME":
                                    builder.cname(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "MX":
                                    builder.mx(
                                        rec.name,
                                        rec.value,
                                        priority=rec.priority or 10,
                                        ttl=rec.ttl,
                                    )
                                elif rec.type == "TXT":
                                    builder.txt(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "NS":
                                    builder.ns(rec.name, rec.value, ttl=rec.ttl)
                                elif rec.type == "URL":
                                    # URL type is 302 redirect
                                    builder.url(
                                        rec.name,
                                        rec.value,
                                        redirect_type="301",
                                        ttl=rec.ttl,
                                    )
                                    builder._records[
                                        -1
                                    ].type = "URL"  # Override to use URL instead of URL301
                                elif rec.type == "URL301":
                                    builder.url(
                                        rec.name,
                                        rec.value,
                                        redirect_type="301",
                                        ttl=rec.ttl,
                                    )
                                elif rec.type == "FRAME":
                                    builder.url(
                                        rec.name,
                                        rec.value,
                                        redirect_type="frame",
                                        ttl=rec.ttl,
                                    )

                            # Save to Namecheap
                            self.nc.dns.set(self.current_domain, builder)

                            if self.is_running:
                                self.call_from_thread(
                                    self.update_status,
                                    f"✅ Deleted {record.type} record successfully!",
                                )
                                # Reload to get fresh data
                                self.call_from_thread(self.load_records_async)
                        except Exception as e:
                            if self.is_running:
                                self.call_from_thread(
                                    self.update_status, f"❌ Error deleting record: {e}"
                                )
                                # Add back the record on failure
                                self.records.append(record)

                    thread = threading.Thread(target=delete, daemon=True)
                    self._threads.append(thread)
                    thread.start()

            # Show confirmation modal
            message = f"Delete {record.type} record '{record.name}'?"
            self.push_screen(ConfirmModal(message), handle_confirm)

    def update_status(self, message: str) -> None:
        """Update status bar."""
        self.query_one("#status", Static).update(message)

    def action_escape(self) -> None:
        """Handle escape key - unfocus current widget."""
        focused = self.focused
        if focused:
            self.set_focus(None)
        else:
            # If nothing focused, focus the domain selector
            self.query_one("#domain-select", Select).focus()


def main() -> None:
    """Run the DNS Manager."""
    try:
        app = DNSManagerApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
