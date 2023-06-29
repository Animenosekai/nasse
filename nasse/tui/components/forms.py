"""Form components"""
import typing

from textual.containers import Horizontal, Container
from textual.reactive import reactive
from textual.widgets import Input, Label, Select

from nasse.models import UserSent
from nasse.tui.widget import Widget
from nasse.tui.components.texts import SectionTitle


class UserSentInput(Widget):
    """The input component for a user sent value"""
    value: reactive[typing.Optional[UserSent]] = reactive(None)

    DEFAULT_CSS = """
    UserSentInput {
        height: auto;
        margin: 1 0 1 0;
    }

    .form-input-container {
        height: auto;
    }

    .form-input-name {
        width: 15%;
        height: auto;
    }

    .form-input-value {
        width: 80%;
        height: auto;
    }

    .form-input-description {
        text-opacity: 0.5;
    }
    """
    input_name: reactive[str] = reactive(None)
    input_value: reactive[str] = reactive(None)

    def __init__(self,
                 value: typing.Optional[UserSent] = None,
                 inputs: typing.Optional[typing.Set[UserSent]] = None,
                 on_change: typing.Optional[typing.Callable[["UserSentInput", typing.Optional[str], typing.Optional[str]], typing.Any]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = value
        self.inputs = inputs or set()
        self.on_change = on_change

    def compose(self):
        if not self.inputs:
            with Horizontal(classes="form-input-container"):
                yield Input(placeholder="name", classes="form-input-name", name="input-name")
                yield Input(placeholder="value", classes="form-input-value", name="input-value")
            return

        with Horizontal(classes="form-input-container"):
            if not self.value:
                non_required = [(element.name, element)
                                for element in self.inputs if not element.required]
                if non_required:
                    yield Select(non_required, classes="form-input-name", name="input-name")
                    yield Input(disabled=True, classes="form-input-value", name="input-value")
                return
            yield Select([(element.name, element) for element in self.inputs],
                         value=self.value,
                         disabled=self.value.required,
                         classes="form-input-name",
                         name="input-name")
            yield Input(placeholder=self.value.type.__name__
                        if hasattr(self.value.type, "__name__") else str(self.value.type),
                        classes="form-input-value",
                        name="input-value")
        yield Label(self.value.description, classes="form-input-description")

    def on_input_changed(self, event: Input.Changed) -> None:
        """When an input changed"""
        if event.input.name == "input-name":
            self.input_name = event.input.value
        elif event.input.name == "input-value":
            self.input_value = event.input.value

        if self.on_change:
            self.on_change(self, self.input_name, self.input_value)

    def on_select_changed(self, event: Select.Changed) -> None:
        """When a Select object changed"""
        if event.input.name == "input-name":
            self.input_name = event.select.value

        if self.on_change:
            self.on_change(self, self.input_name, self.input_value)


class UserSentForm(Widget):
    """A form for user sent inputs"""

    DEFAULT_CSS = """
    UserSentForm {
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }

    .form-inputs-container {
        height: auto;
    }

    .form-buttons {
        height: auto;
        align-horizontal: right;
    }

    .form-buttons-add {
        background: rgb(0, 162, 255);
        color: white;
    }

    .form-buttons-remove {
        opacity: 0.75;
    }
    """

    def __init__(self, title: str, inputs: typing.Optional[typing.Set[UserSent]] = None, multiple: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.inputs = inputs or set()
        self.multiple = multiple

    def compose(self):
        yield SectionTitle(self.title)

        for element in self.inputs:
            if element.required:
                yield UserSentInput(element, inputs=self.inputs)

        with Container(classes="form-inputs-container"):
            yield UserSentInput(None, self.inputs, self.on_change)

    #     with Horizontal(classes="form-buttons"):
    #         yield Button("Add", name="add", classes="form-buttons-add")
    #         yield Button("Remove", name="remove", classes="form-buttons-remove")

    def on_change(self, user_input: UserSentInput, name: typing.Optional[str] = None, value: typing.Optional[str] = None):
        """When something changed in any user input"""
        last_element: UserSentInput = self.query_one(".form-inputs-container", Container).query(UserSentInput).last()

        for element in self.query_one(".form-inputs-container", Container).query(UserSentInput)[:-1]:
            if not element.input_name and not element.input_value:
                element.remove()

        if last_element.input_name or last_element.input_value:
            self.query_one(".form-inputs-container", Container).mount(UserSentInput(None, self.inputs, self.on_change))

    @property
    def values(self):
        """Returns the rendered values"""
        results = {}
        # pylint: disable=not-an-iterable
        for element in self.query(UserSentInput):
            # if element.input_name and element.input_value:
            if element.input_name:
                if self.multiple:
                    try:
                        results[element.input_name].append(element.input_value)
                    except KeyError:
                        results[element.input_name] = [element.input_value]
                else:
                    results[element.input_name] = element.input_value
        return results

    # def on_button_pressed(self, event: Button.Pressed) -> None:
    #     """When a button is pressed"""
    #     if event.button.name == "add":
    #         self.query_one(".form-inputs-container", Container).mount(UserSentInput(None, self.inputs))
    #     elif event.button.name == "remove":
    #         self.query_one(".form-inputs-container", Container).query(UserSentInput).last().remove()
