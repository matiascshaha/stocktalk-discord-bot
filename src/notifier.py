class Notifier:
    """Handle notifications for parsed signals."""

    def notify(self, parsed_message, author):
        if not parsed_message:
            return

        self._print_console_notification(parsed_message, author)

    def _signal_objs(self, parsed_message):
        return parsed_message.get("signals", []) if isinstance(parsed_message, dict) else []

    def _print_console_notification(self, parsed_message, author):
        print("\n" + "=" * 60)
        print(f"📊 STOCK SIGNAL DETECTED from {author}")
        print("=" * 60)

        signal_objs = self._signal_objs(parsed_message)
        for i, signal in enumerate(signal_objs, 1):
            print(f"\nSignal #{i}:")
            print(f"  Ticker: {signal.get('ticker')}")
            print(f"  Action: {signal.get('action')}")
            print(f"  Confidence: {float(signal.get('confidence', 0.0))*100:.1f}%")
            if signal.get("weight_percent") is not None:
                print(f"  Weight: {signal.get('weight_percent')}%")
            print(f"  Urgency: {signal.get('urgency')}")
            print(f"  Sentiment: {signal.get('sentiment')}")
            print(f"  Reasoning: {signal.get('reasoning')}")

            vehicles = signal.get("vehicles") or []
            if vehicles:
                vehicle_types = [v.get("type") for v in vehicles if isinstance(v, dict)]
                print(f"  Vehicles: {', '.join([v for v in vehicle_types if v])}")

        print("=" * 60 + "\n")
