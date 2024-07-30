import httpx

from textual import work, events, on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static, Button, TextArea
from typing import Optional, Any

_URL = "http://localhost:8000/api"

class GameScreen(Screen):

    CSS = """
    Container {
        border: solid green;
    }

    TextArea {
        height: 80%;
        width: 50%;
    }

    #header {
        height: 20%;
    }

    #main {
        height: 80%;
        layout: grid;
        grid-size: 3;
    }

    #editors {
        column-span: 2;
        width: 100%;
        height: 100%;
    }
    """

    game_session: Optional[str] = None
    playing: bool = False
    game_over: bool = False
    last_response: httpx.Response = None

    title_widget = Static()
    subtitle_widget = Static()
    lives_widget = Static()
    score_widget = Static()

    start_button = Button("(Space) Start", variant="primary", id="start")
    accept_button = Button("(y) Accept", variant="success", id="accept")
    deny_button = Button("(n) Deny", variant="error", id="deny")

    left_code_pane = None
    right_code_pane = None

    def compose(self) -> ComposeResult:
        yield Container(id="header")
        yield Container(
            Horizontal(id="editors"),
            Container(id="sidebar"),
            id="main"
        )

    def on_mount(self) -> None:
        self.new_game()

    def update(self, context: httpx.Response):
        self.update_header(context)
        self.update_sidebar(context)
        self.update_editors(context)
        self.gamestate_check(context)

    def update_header(self, context: httpx.Response):
        header_container = self.query_one("#header")
        _widgets = [self.title_widget, self.subtitle_widget]
        for w in _widgets:
            if not w.is_mounted:
                header_container.mount(w)

        obj = context.json()
        if not obj["current_level"]:
            self.title_widget.update("Please press Start...")
            self.subtitle_widget.update("")
        elif obj["lives"] <= 0 or self.game_over:
            self.title_widget.update("Game Over!")
            self.subtitle_widget.update("Try again by pressing Start.")
        else:
            level = obj['current_level']
            prompt = obj['current_prompt']
            title = f"{level['repo_id']} ({level['prompt_number']}/{level['max_prompts']})"
            self.title_widget.update(f"[green]{title}[/]")
            self.subtitle_widget.update(f"{prompt['title']}")
    
    def update_sidebar(self, context: httpx.Response):
        sidebar_container = self.query_one("#sidebar")
        _text_widgets = [self.lives_widget, self.score_widget]
        for w in _text_widgets:
            if not w.is_mounted:
                sidebar_container.mount(w)

        obj = context.json()

        lives = obj['lives']
        lives_str = f"{'[red blink]' if lives == 1 else ''}{lives}{'[/]' if lives == 1 else ''}"

        self.lives_widget.update(f"Lives: {lives_str}")
        self.score_widget.update(f"Score: {obj['score']}")
        
        _idle_buttons = [self.start_button]
        _active_buttons = [self.accept_button, self.deny_button]

        if not obj["current_level"] or self.game_over:
            if any(map(lambda w: w.is_mounted, _active_buttons)):
                sidebar_container.remove_children(_active_buttons)
                sidebar_container.mount_all(_idle_buttons)
            elif not any(map(lambda w: w.is_mounted, _idle_buttons)):
                sidebar_container.mount_all(_idle_buttons)
        else:
            if any(map(lambda w: w.is_mounted, _idle_buttons)):
                sidebar_container.remove_children(_idle_buttons)
                sidebar_container.mount_all(_active_buttons)

    def update_editors(self, context: httpx.Response):
        if any(map(lambda w: w == None, [self.left_code_pane, self.right_code_pane])):
            self.left_code_pane = TextArea(language="python",
                                    read_only=True,
                                    show_line_numbers=True)
            self.right_code_pane = TextArea(language="python",
                                    read_only=True,
                                    show_line_numbers=True)

        editors_container = self.query_one("#editors")
        _editor_widgets = [self.left_code_pane, self.right_code_pane]

        obj = context.json()

        if not obj["current_level"] or self.game_over:
            for w in _editor_widgets:
                w.load_text("")
        else:
            for w in _editor_widgets:
                if not w.is_mounted:
                    editors_container.mount(w)
            self.left_code_pane.load_text(obj["current_prompt"]["file_a_contents"])
            self.right_code_pane.load_text(obj["current_prompt"]["file_b_contents"])

    def gamestate_check(self, context: httpx.Response):
        obj = context.json()
        if not obj["current_level"] and self.playing:
            self.playing = False
        if obj["lives"] <= 0:
            self.end()

    @work
    async def new_game(self):
        url = f"{_URL}/new"
        async with httpx.AsyncClient(timeout=None) as client:
            resp: httpx.Response = await client.get(url)
            session = resp.json()
            self.game_session = session["id"]
            self.game_over = False
        self.update(resp)

    @work
    async def start_level(self):
        self.loading = True
        if self.game_over:
            worker = self.new_game()
            await worker.wait()
        url = f"{_URL}/genlevel/{self.game_session}"
        async with httpx.AsyncClient(timeout=None) as client:
            resp: httpx.Response = await client.get(url)
            self.last_response = resp
        self.playing = True
        self.update(resp)
        self.loading = False

    @work
    async def submit(self, ans: bool):
        url = f"{_URL}/submit/{self.game_session}/"
        url += "yes" if ans else "no"
        async with httpx.AsyncClient(timeout=None) as client:
            resp: httpx.Response = await client.get(url)
            self.last_response = resp
        self.update(resp)

    @on(Button.Pressed, "#start")
    def start(self):
        if not self.playing:
            self.start_level()

    @on(Button.Pressed, "#accept")
    def accept(self):
        if self.playing:
            self.submit(True)

    @on(Button.Pressed, "#deny")
    def deny(self):
        if self.playing:
            self.submit(False)

    def end(self):
        if self.playing:
            self.playing = False
            self.game_over = True
            self.update(self.last_response)

    def on_key(self, event: events.Key) -> None:
        if event.key == "space":
            self.start()
        elif event.key == "y":
            self.accept()
        elif event.key == "n":
            self.deny()
        elif event.key == "escape":
            self.end()
