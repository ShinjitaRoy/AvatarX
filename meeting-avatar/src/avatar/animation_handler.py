class AnimationHandler:
    def __init__(self):
        self.running = False
        self.current = None

    def start_animation(self, name: str) -> bool:
        """Start a simple animation (stub)."""
        self.current = name
        self.running = True
        return True

    def stop_animation(self) -> bool:
        """Stop current animation (stub)."""
        self.current = None
        self.running = False
        return True