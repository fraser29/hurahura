import os
from nicegui import ui, app
from miresearch import mi_subject
from miresearch.miresearchui import miui_helpers
import inspect

os.environ["QT_QPA_PLATFORM"] = "offscreen"

@ui.page('/settings_page')
def settings_page():
    page = SettingsPage()
    page.build_page()


class SettingsPage:
    def __init__(self):
        self.DEBUG = True
        self.inputs = {}  # Dictionary to store input references

    def build_page(self):
        """Opens a modal dialog with settings configuration options"""
        with ui.column().classes('w-full items-center'):
            with ui.card().classes('w-3/4 p-4'):
                ui.label('Config File Builder Helper').classes('text-h4 text-center mb-4')
                
                # Store input references in self.inputs
                labels = ['A', 'B', 'C', 'D', 'E', 'F']
                for label in labels:
                    with ui.row().classes('w-full items-center gap-4'):
                        ui.label(f'Label {label}').classes('w-32')
                        ui.label(f'Example {label}').classes('w-48 text-gray-600')
                        self.inputs[label] = ui.input(f'Input {label}').classes('w-64')

                # Add save button at the bottom
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Save Configuration', on_click=self.save_config).classes('bg-blue-500 text-white')

    def save_config(self):
        """Save the configuration to a .conf file"""
        try:
            # Create config content
            config_content = ""
            for label, input_field in self.inputs.items():
                if input_field.value:  # Only write non-empty values
                    config_content += f"Label_{label}={input_field.value}\n"

            # Ask user for file name
            def save_file(filename: str):
                if not filename.endswith('.conf'):
                    filename += '.conf'
                
                with open(filename, 'w') as f:
                    f.write(config_content)
                ui.notify(f'Configuration saved to {filename}', type='positive')

            # Create a dialog for filename input
            with ui.dialog() as dialog, ui.card():
                ui.label('Enter filename for configuration:')
                filename_input = ui.input('Filename').classes('w-64')
                with ui.row():
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    ui.button('Save', on_click=lambda: [save_file(filename_input.value), dialog.close()])
                dialog.open()

        except Exception as e:
            ui.notify(f'Error saving configuration: {str(e)}', type='negative')

        
