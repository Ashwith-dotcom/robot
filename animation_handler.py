import pygame
import os
from PIL import Image, ImageSequence
import time

os.environ["SDL_VIDEODRIVER"] = "x11"
os.environ["SDL_AUDIODRIVER"] = "alsa"

class AnimationHandler:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.mixer.quit()

        # Get screen info and set up display
        screen_info = pygame.display.Info()
        self.SCREEN_WIDTH = screen_info.current_w
        self.SCREEN_HEIGHT = screen_info.current_h
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 
                                            pygame.SWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("AI Assistant")
        self.clock = pygame.time.Clock()

        self.frames = []
        self.durations = []
        self.frame_index = 0
        self.frame_count = 0
        self.animation_state = 'idle'

        # Animation paths
        self.GIF_PATHS = {
            'idle': '/home/dlt/chatbot/animations/idle.gif',
            'listening': '/home/dlt/chatbot/animations/listening.gif',
            'thinking': '/home/dlt/chatbot/animations/thinking.gif',
            'answering': '/home/dlt/chatbot/animations/speaking.gif',
            'last': '/home/dlt/chatbot/animations/last.gif'
        }

        # Create state file if it doesn't exist
        self.STATE_FILE = "animation_state.txt"
        with open(self.STATE_FILE, "w") as f:
            f.write("idle")

    def load_gif(self, path):
        self.frames = []
        self.durations = []
        try:
            pil_gif = Image.open(path)
            for frame in ImageSequence.Iterator(pil_gif):
                mode = frame.mode
                size = frame.size
                data = frame.tobytes()

                pygame_frame = pygame.image.fromstring(data, size, mode)
                scaled_frame = pygame.transform.scale(pygame_frame,
                    (self.SCREEN_WIDTH, int(self.SCREEN_WIDTH * size[1] / size[0])))

                self.frames.append(scaled_frame)
                self.durations.append(frame.info.get('duration', 100))

            self.frame_index = 0
            self.frame_count = 0
            print(f"Successfully loaded GIF: {path}")
        except Exception as e:
            print(f"Error loading GIF: {e}")

    def check_state_file(self):
        try:
            with open(self.STATE_FILE, "r") as f:
                new_state = f.read().strip()
                if new_state != self.animation_state:
                    self.animation_state = new_state
                    self.load_gif(self.GIF_PATHS[new_state])
        except Exception as e:
            print(f"Error reading state file: {e}")

    def run(self):
        self.load_gif(self.GIF_PATHS['idle'])
        running = True

        while running:
            try:
                # Check for new animation state from file
                self.check_state_file()

                if not self.frames:
                    time.sleep(0.016)
                    continue

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break

                frame_intervals = [max(1, int(d / (1000 / 60))) for d in self.durations]
                x_pos = (self.SCREEN_WIDTH - self.frames[0].get_width()) // 2
                y_pos = (self.SCREEN_HEIGHT - self.frames[0].get_height()) // 2

                self.screen.fill((0, 0, 0))
                self.screen.blit(self.frames[self.frame_index], (x_pos, y_pos))
                pygame.display.flip()

                self.frame_count += 1
                if self.frame_count >= frame_intervals[self.frame_index]:
                    self.frame_index = (self.frame_index + 1) % len(self.frames)
                    self.frame_count = 0

                self.clock.tick(60)

            except Exception as e:
                print(f"Error in animation loop: {e}")
                time.sleep(0.016)

        if os.path.exists(self.STATE_FILE):
            os.remove(self.STATE_FILE)
        pygame.quit()

if __name__ == "__main__":
    handler = AnimationHandler()
    handler.run()