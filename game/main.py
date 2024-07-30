from textual.app import App

from .screens.menu import MenuScreen
from .screens.game import GameScreen

class GameWindow(App):
    
    SCREENS = {
        "menu": MenuScreen(),
        "game": GameScreen()
    }

    def on_mount(self) -> None:
        self.push_screen("menu")

if __name__ == "__main__":
    GameWindow().run()
