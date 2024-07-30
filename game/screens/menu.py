from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Center
from textual.widgets import Label, Button

class MenuScreen(Screen):

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-gutter: 2;
        padding: 2;
    }
    
    Label {
        width: 100%;
        height: 50%;
        content-align: center bottom;
        text-style: bold;
    }

    Button {
        width: 50%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Patches Please")
        yield Center(Button.success("Start"))

    def on_button_pressed(self, _) -> None:
        # TODO: Change to game screen
        self.app.switch_screen("game")
        pass
